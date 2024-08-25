use crate::models::extraction::segment::Segment;
use actix_multipart::form::{tempfile::TempFile, MultipartForm};
use image::{DynamicImage, RgbaImage};
use poppler::{Document as PopplerDocument, Page as PopplerPage};
use serde::Deserialize;
use std::io::Read;
use std::path::PathBuf;

#[derive(Debug, MultipartForm)]
pub struct PdfUploadForm {
    #[multipart(limit = "100MB")]
    pub file: TempFile,
    pub page_number: i32,
    pub bounding_boxes: Vec<Segment>, // Array of Segments
}

pub fn extract_pdf_snippets(
    form: PdfUploadForm,
) -> Result<Vec<DynamicImage>, Box<dyn std::error::Error>> {
    let mut pdf_file = form.file;
    let page_number = form.page_number;
    let segments = form.bounding_boxes;

    // Read the PDF content into memory
    let mut pdf_content = Vec::new();
    pdf_file.file.read_to_end(&mut pdf_content)?;

    // Load the PDF document from memory
    let doc = PopplerDocument::new_from_data(&pdf_content, None)?;

    // Get the specified page (0-indexed in Poppler)
    let page = doc.page(page_number - 1).ok_or("Page not found")?;

    // Get page dimensions
    let (width, height) = page.size();

    // Create a full page image
    let mut full_page_img = RgbaImage::new(width as u32, height as u32);

    // Render the full page
    page.render(
        full_page_img.as_mut(),
        poppler::PopplerRectangle {
            x1: 0.0,
            y1: 0.0,
            x2: width,
            y2: height,
        },
        poppler::CairoScale { x: 1.0, y: 1.0 },
        poppler::Rotation::Upright,
    );

    // Convert to DynamicImage for easier manipulation
    let full_page_dynamic = DynamicImage::ImageRgba8(full_page_img);

    // Extract snippets based on segments
    let snippets: Vec<DynamicImage> = segments
        .iter()
        .map(|segment| {
            let x = segment.left as u32;
            let y = segment.top as u32;
            let w = segment.width as u32;
            let h = segment.height as u32;
            full_page_dynamic.crop(x, y, w, h)
        })
        .collect();

    Ok(snippets)
}

#[cfg(test)]
mod tests {
    use super::*;
    use actix_multipart::form::tempfile::TempFile;
    use std::fs::File;
    use std::io::Read;

    #[test]
    fn test_extract_pdf_snippets() {
        // Load the PDF file
        let mut pdf_file =
            File::open("tests/fixtures/sample.pdf").expect("Failed to open PDF file");
        let mut pdf_content = Vec::new();
        pdf_file
            .read_to_end(&mut pdf_content)
            .expect("Failed to read PDF content");

        // Create mock segments
        let segments = vec![
            Segment {
                left: 0,
                top: 0,
                width: 100,
                height: 100,
            },
            // Add more segments as needed
        ];

        // Create a mock PdfUploadForm
        let form = PdfUploadForm {
            file: TempFile::new(pdf_content),
            page_number: 1,
            bounding_boxes: segments,
        };

        // Call the extract_pdf_snippets function
        let result = extract_pdf_snippets(form);

        // Assert that the function succeeded
        assert!(result.is_ok());

        let snippets = result.unwrap();

        // Assert that we have the correct number of snippets
        assert_eq!(snippets.len(), 1); // Adjust based on the number of segments

        // Add more specific assertions as needed
    }
}
