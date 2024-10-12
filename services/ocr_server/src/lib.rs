use actix_cors::Cors;
use actix_multipart::form::MultipartFormConfig;
use actix_multipart::MultipartError;
use actix_web::middleware::Logger;
use actix_web::Error;
use actix_web::HttpRequest;
use actix_web::{ web, App, HttpServer };
use env_logger::Env;

pub mod routes;

use routes::health::health_check;

pub fn main() -> std::io::Result<()> {
    actix_web::rt::System::new().block_on(async move {
        fn handle_multipart_error(err: MultipartError, _: &HttpRequest) -> Error {
            println!("Multipart error: {}", err);
            Error::from(err)
        }

        let max_size: usize = std::env
            ::var("MAX_TOTAL_LIMIT")
            .unwrap_or_else(|_| "10485760".to_string())
            .parse()
            .expect("MAX_TOTAL_LIMIT must be a valid usize");
        let max_memory_size: usize = std::env
            ::var("MAX_MEMORY_LIMIT")
            .unwrap_or_else(|_| "10485760".to_string())
            .parse()
            .expect("MAX_MEMORY_LIMIT must be a valid usize");
        let timeout: usize = std::env
            ::var("TIMEOUT")
            .unwrap_or_else(|_| "600".to_string())
            .parse()
            .expect("TIMEOUT must be a valid usize");
        let timeout = std::time::Duration::from_secs(timeout.try_into().unwrap());

        env_logger::init_from_env(Env::default().default_filter_or("info"));

        HttpServer::new(move || {
            App::new()
                .wrap(Cors::permissive())
                .wrap(Logger::default())
                .wrap(Logger::new("%a %{User-Agent}i"))
                .app_data(
                    MultipartFormConfig::default()
                        .total_limit(max_size)
                        .memory_limit(max_memory_size)
                        .error_handler(handle_multipart_error)
                )
                .route("/", web::get().to(health_check))
        })
            .bind("0.0.0.0:8000")?
            .keep_alive(timeout)
            .run().await
    })
}
