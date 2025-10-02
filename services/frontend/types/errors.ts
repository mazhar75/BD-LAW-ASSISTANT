export interface ApiError {
  response?: {
    status: number;
    data?: {
      message?: string;
      error?: string;
      details?: string;
      field?: string;
    };
  };
  message?: string;
}

export interface FormError {
  message: string;
  type?: string;
}