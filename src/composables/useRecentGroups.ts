import { ref } from 'vue';

const STORAGE_KEY = 'poli-rasp:recent-groups';
const MAX_RECENT = 5;

export interface GroupRef {
  uuid: string;
  number: string;
}

export function useRecentGroups() {
  const recentGroups = ref<GroupRef[]>(loadFromStorage());

  function loadFromStorage(): GroupRef[] {
    if (typeof localStorage === 'undefined') return [];
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  }

  function saveToStorage(groups: GroupRef[]) {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(groups));
  }

  function addRecentGroup(group: GroupRef) {
    const filtered = recentGroups.value.filter(g => g.uuid !== group.uuid);
    const updated = [group, ...filtered].slice(0, MAX_RECENT);
    recentGroups.value = updated;
    saveToStorage(updated);
  }

  function clearRecentGroups() {
    recentGroups.value = [];
    saveToStorage([]);
  }

  return { recentGroups, addRecentGroup, clearRecentGroups };
}
