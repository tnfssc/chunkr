use crate::models::server::auth::UserInfo;
use crate::models::server::tasks::TasksQuery;
use crate::utils::configs::s3_config::ExternalS3Client;
use crate::utils::db::deadpool_postgres::Pool;
use crate::utils::server::get_tasks::get_tasks;
use actix_web::{web, Error, HttpResponse};
use aws_sdk_s3::Client as S3Client;

pub async fn get_tasks_status(
    pool: web::Data<Pool>,
    s3_client: web::Data<S3Client>,
    s3_external_client: web::Data<ExternalS3Client>,
    query: web::Query<TasksQuery>,
    user_info: web::ReqData<UserInfo>,
) -> Result<HttpResponse, Error> {
    let page = query.page.unwrap_or(1);
    let limit = query.limit.unwrap_or(10);

    let tasks = get_tasks(
        &pool,
        &s3_client,
        &s3_external_client.0,
        user_info.user_id.clone(),
        page,
        limit,
    )
    .await?;
    Ok(HttpResponse::Ok().json(tasks))
}
