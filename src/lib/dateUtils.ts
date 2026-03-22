export interface DateLabel {
  text: string;
  colorClass: string;
  sortPriority: number; // 0=сегодня, 1=завтра, 2=ближайшие, 3=далеко, 4=прошло
}

/**
 * Возвращает количество дней от сегодня до даты пересдачи.
 * Отрицательное значение — пересдача уже прошла.
 */
export function daysUntil(dateStr: string): number {
  const [y, m, d] = dateStr.split('-').map(Number);
  const target = new Date(y, m - 1, d);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

/**
 * Возвращает текст и цвет бейджа для даты пересдачи.
 */
export function getDateLabel(dateStr: string): DateLabel {
  const days = daysUntil(dateStr);

  if (days < 0) {
    return {
      text: 'Прошёл',
      colorClass: 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500',
      sortPriority: 4,
    };
  }
  if (days === 0) {
    return {
      text: 'Сегодня',
      colorClass: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300',
      sortPriority: 0,
    };
  }
  if (days === 1) {
    return {
      text: 'Завтра',
      colorClass: 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300',
      sortPriority: 1,
    };
  }
  if (days <= 6) {
    return {
      text: `Через ${days} дн.`,
      colorClass: 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300',
      sortPriority: 2,
    };
  }
  return {
    text: `Через ${days} дн.`,
    colorClass: 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400',
    sortPriority: 3,
  };
}
