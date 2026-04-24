package models

// ErrorResponse структура ошибки
type ErrorResponse struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// ResponseAPI общая структура ответа API
type ResponseAPI struct {
	Success   bool          `json:"success"`
	RequestId string        `json:"requestId"`
	Message   string        `json:"message"`
	Result    interface{}   `json:"result"`
	Errors    ErrorResponse `json:"errors"`
}
