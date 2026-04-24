package scheduleParser

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"raspyx2/internal/models"
)

func (p *ScheduleParser) ParseGroupSchedule(data *models.ParseGroupScheduleData) (*models.ParseScheduleResponse, error) {
	req, err := http.NewRequestWithContext(
		p.Ctx,
		"GET", fmt.Sprintf("https://rasp.dmami.ru/site/group?group=%v&session=%v", data.Group, data.IsSession),
		nil,
	)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Referer", "https://rasp.dmami.ru/")

	resp, err := p.Client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var r models.ParseScheduleResponse
	if err := json.Unmarshal(raw, &r); err != nil {
		return nil, fmt.Errorf("error unmarshling response %v: %v", r, err)
	}

	if r.Status != "ok" {
		if r.Message != "Не нашлось расписание для группы" {
			return nil, fmt.Errorf("unknown response error: %v", r.Message)
		}
	}

	return &r, nil
}
