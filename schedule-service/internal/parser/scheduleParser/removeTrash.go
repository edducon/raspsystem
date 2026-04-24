package scheduleParser

import (
	"regexp"
	"strings"
)

func (p *ScheduleParser) RemoveTrash(s string) string {
	return strings.TrimSpace(removeEmojis(removeHTML(s)))
}

func removeEmojis(text string) string {
	emojiRegex := regexp.MustCompile(`[\x{1F600}-\x{1F64F}]|[\x{1F300}-\x{1F5FF}]|[\x{1F680}-\x{1F6FF}]|[\x{2600}-\x{26FF}]|[\x{2700}-\x{27BF}]`)
	return strings.TrimSpace(emojiRegex.ReplaceAllString(text, ""))
}

func removeHTML(text string) string {
	htmlRegex := regexp.MustCompile(`>.*<`)
	newText := htmlRegex.FindString(text)
	if newText == "" {
		return text
	}
	return strings.TrimSpace(newText[1 : len(newText)-1])
}
