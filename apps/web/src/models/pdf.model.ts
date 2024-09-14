export interface PageImage {
  pageNumber: number;
  base64Png: string;
  format: 'png' | 'jpg';
}

export interface ConvertAllPagesResponse {
  pages: PageImage[];
}
