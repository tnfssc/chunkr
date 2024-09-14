use actix_multipart::form::{MultipartForm, text::Text};
use actix_web::{HttpResponse, Error};
use crate::models::server::pdf::PDFFileForm;
use crate::extraction::pdf2png::convert_all_pdf_pages;


pub async fn get_pdf_pages(
    form: MultipartForm<PDFFileForm>,
) -> Result<HttpResponse, Error> {
    let form = form.into_inner();
    let file_data = &form.file;
    let dpi = form.dpi.unwrap_or(Text(150)).into_inner();
    let pages_map = convert_all_pdf_pages(file_data.file.path(), dpi).await?;
    Ok(HttpResponse::Ok().json(pages_map))
}
