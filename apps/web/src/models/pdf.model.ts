export interface PageImage {
  pageNumber: number;
  base64Png: string;
}

export interface ConvertAllPagesResponse {
  pages: PageImage[];
}
