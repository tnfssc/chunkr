import axiosInstance from "./axios.config";
import { ConvertAllPagesResponse } from "../models/pdf.model";

export async function convertAllPages(inputFileUrl: string, dpi: number = 150, format: 'png' | 'jpg' = "png", splitPages: boolean = true) {
    const response = await fetch(inputFileUrl);
    const blob = await response.blob();
    const file = new File([blob], 'document.pdf', { type: 'application/pdf' });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("dpi", dpi.toString());
    formData.append("format", format);
    formData.append("split_pages", splitPages.toString());
    const { data } = await axiosInstance.post<ConvertAllPagesResponse>("/api/pdf/pages", formData);
    return data;
  }