package teachers

import (
	"database/sql"
	"errors"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Получение преподавателей
// @Description Получение списка всех преподавателей в системе
// @Security ApiKeyAuth
// @Tags teachers
// @Accept application/json
// @Produce application/json
// @Success 200 {object} models.ResponseAPI{result=[]models.GetTeacherResponse} "Данные о преподавателях успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/teachers [get]
func (h *TeachersHandler) GetAllTeachers(ctx *gin.Context) {
	GetAllTeachers, GetAllTeachersError := h.service.TeachersService.GetAllTeachers()

	if GetAllTeachersError != nil {
		messageError := fmt.Sprintf("Error get list teachers: %s", GetAllTeachersError.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get list teachers",
		Result:    GetAllTeachers,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение преподавателя по его ФИО
// @Description Получение информации о преподавателе по его teacher_fio
// @Security ApiKeyAuth
// @Tags teachers
// @Accept application/json
// @Produce application/json
// @Param teacher_fio path string true "ФИО преподавателя"
// @Success 200 {object} models.ResponseAPI{result=[]models.GetTeacherResponse} "Данные о преподавателе успешно получены"
// @Failure 404 {object} models.ResponseAPI "Преподаватель не найден"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/teachers/fio/{teacher_fio} [get]
func (h *TeachersHandler) GetTeachersByFio(ctx *gin.Context) {
	teacherFio := ctx.Param("teacher_fio")
	getTeacher, getTeacherError := h.service.TeachersService.GetTeachersByFio(strings.TrimSpace(teacherFio))
	if getTeacherError != nil {
		if errors.Is(getTeacherError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Teacher not found: %s", teacherFio)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get teacher %s: %s", teacherFio, getTeacherError)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get teacher",
		Result:    getTeacher,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение преподавателя по идентификатору
// @Description Получение информации о преподавателе по её teacher_uuid
// @Security ApiKeyAuth
// @Tags teachers
// @Accept application/json
// @Produce application/json
// @Param teacher_uuid path string true "Идентификатор преподавателя"
// @Success 200 {object} models.ResponseAPI{result=models.GetTeacherResponse} "Данные о преподавателе успешно получены"
// @Failure 404 {object} models.ResponseAPI "Преподаватель не найден"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/teachers/uuid/{teacher_uuid} [get]
func (h *TeachersHandler) GetTeacherByUUID(ctx *gin.Context) {
	teacherUUID := ctx.Param("teacher_uuid")
	getTeacher, getTeacherError := h.service.TeachersService.GetTeacherByUUID(teacherUUID)
	if getTeacherError != nil {
		if errors.Is(getTeacherError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Teacher not found: %s", teacherUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get teacher: %s", teacherUUID)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get teacher",
		Result:    getTeacher,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
