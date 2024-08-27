use crate::models::rrq::produce::ProducePayload;
use crate::models::{
    extraction::extract::{ExtractionPayload, ModelInternal},
    extraction::task::{Status, TaskResponse},
};
use crate::utils::configs::extraction_config::Config;
use crate::utils::db::deadpool_postgres::{Client, Pool};
use crate::utils::rrq::service::produce;
use crate::utils::storage::services::upload_to_s3;
use actix_multipart::form::tempfile::TempFile;
use aws_sdk_s3::Client as S3Client;
use chrono::{DateTime, Utc};
use lopdf::Document;
use std::error::Error;
use uuid::Uuid;

fn is_valid_pdf(buffer: &[u8]) -> Result<bool, lopdf::Error> {
    match Document::load_mem(buffer) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

async fn produce_extraction_payloads(
    extraction_payload: ExtractionPayload,
) -> Result<(), Box<dyn Error>> {
    let config = Config::from_env()?;

    let produce_payload = ProducePayload {
        queue_name: config.extraction_queue,
        publish_channel: None,
        payload: serde_json::to_value(extraction_payload).unwrap(),
        max_attempts: None,
        item_id: Uuid::new_v4().to_string(),
    };

    produce(vec![produce_payload]).await?;

    Ok(())
}

pub async fn create_task(
    pool: &Pool,
    s3_client: &S3Client,
    file: &TempFile,
    task_id: String,
    user_id: String,
    api_key: &String,
    model: ModelInternal,
) -> Result<TaskResponse, Box<dyn Error>> {
    let mut client: Client = pool.get().await?;
    let config = Config::from_env()?;
    let created_at: DateTime<Utc> = Utc::now();
    let expiration_time: Option<DateTime<Utc>> = config.task_expiration.map(|exp| Utc::now() + exp);

    let buffer: Vec<u8> = std::fs::read(file.file.path())?;

    if !is_valid_pdf(&buffer)? {
        return Err("Not a valid PDF".into());
    }

    let file_size = file.size;
    let page_count = match Document::load_mem(&buffer) {
        Ok(doc) => doc.get_pages().len() as i32,
        Err(_) => return Err("Unable to count pages".into()),
    };

    // Check current usage and limit
    let usage_row = client.query_one(
        "SELECT COALESCE(SUM(usage), 0) as total_usage FROM public.api_key_usage WHERE api_key = $1 AND usage_type = 'page_count'",
        &[&api_key]
    ).await?;
    let current_usage: i64 = usage_row.get("total_usage");

    let limit_row = client.query_opt(
        "SELECT usage_limit FROM public.api_key_limit WHERE api_key = $1 AND usage_type = 'page_count' LIMIT 1",
        &[&api_key]
    ).await?;
    let usage_limit: i64 = limit_row
        .map(|row| row.get("usage_limit"))
        .unwrap_or(i64::MAX);

    if current_usage + i64::from(page_count) > usage_limit {
        return Err(format!(
            "Adding a task with {} pages would exceed the usage limit of {} pages",
            page_count.clone(),
            usage_limit.clone()
        )
        .into());
    }

    let file_name = file.file_name.as_deref().unwrap_or("unknown.pdf");
    let s3_path = format!(
        "s3://{}/{}/{}/{}/{}",
        config.s3_bucket,
        user_id,
        task_id,
        Uuid::new_v4().to_string(),
        file_name
    );
    let output_s3_path = s3_path.replace(".pdf", &format!(".{}", model.get_extension()));
    let task_url = format!("{}/task/{}", config.base_url, task_id);

    upload_to_s3(s3_client, &s3_path, file.file.path()).await?;

    let tx = client.transaction().await?;

    tx.execute(
        "INSERT INTO ingestion_tasks (task_id, file_count, total_size, total_pages, created_at, finished_at, api_key, url, status, model, expiration_time) 
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)",
        &[
            &task_id,
            &1i32,
            &(file_size as i64),
            &page_count,
            &created_at,
            &None::<String>,
            &api_key,
            &task_url,
            &Status::Starting.to_string(),
            &model.to_string(),
            &expiration_time,
        ]
    ).await?;

    tx.execute(
        "INSERT INTO ingestion_files (file_id, task_id, file_name, file_size, page_count, created_at, status, input_location, output_location, model) 
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
        &[
            &Uuid::new_v4().to_string(),
            &task_id,
            &file_name,
            &(file_size as i64),
            &page_count,
            &created_at,
            &Status::Starting.to_string(),
            &s3_path,
            &output_s3_path,
            &model.to_string(),
        ]
    ).await?;

    // Update API key usage
    tx.execute(
        "INSERT INTO public.api_key_usage (api_key, usage, usage_type, service) 
        VALUES ($1, $2, 'page_count', 'ingestion') 
        ON CONFLICT (api_key, usage_type, service) 
        DO UPDATE SET usage = public.api_key_usage.usage + $2",
        &[&api_key, &page_count],
    )
    .await?;

    tx.commit().await?;

    let extraction_payload = ExtractionPayload {
        model: model.clone(),
        input_location: s3_path,
        output_location: output_s3_path,
        expiration: None,
        batch_size: Some(config.batch_size),
        file_id: Uuid::new_v4().to_string(),
        task_id: task_id.clone(),
    };

    produce_extraction_payloads(extraction_payload).await?;

    Ok(TaskResponse {
        task_id: task_id.clone(),
        status: Status::Starting,
        created_at,
        finished_at: None,
        expiration_time,
        file_url: None,
        task_url: Some(task_url),
        message: "Extraction started".to_string(),
        model: model.to_external(),
    })
}
