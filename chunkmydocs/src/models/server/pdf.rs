use actix_multipart::form::{tempfile::TempFile, MultipartForm, text::Text};

#[derive(Debug, MultipartForm)]
pub struct PDFFileForm {
    pub file: TempFile,
    pub dpi: Option<Text<u32>>,
}
