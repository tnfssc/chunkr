use actix_web::HttpResponse;

/// Health Check
///
/// Confirmation that the service can respond to requests
pub async fn health_check() -> HttpResponse {
    let message = "OK";
    HttpResponse::Ok().body(message)
}
