import { useState, useCallback } from 'react';
import { useStore } from '@/store/useStore';
import type { PermissionLevel } from '@/types';

export interface UseEditModeOptions {
  section: 'universal' | 'operations' | 'technical' | 'commercial' | 'strategy' | 'marketing';
  onSave?: () => Promise<void>;
}

export function useEditMode({ section, onSave }: UseEditModeOptions) {
  const { permissions } = useStore();
  const [editingField, setEditingField] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if user can edit this section based on permissions
  const permissionLevel = permissions?.[section] as PermissionLevel | undefined;
  const canEdit = permissionLevel === 'EDIT' || permissionLevel === 'ADMIN' || permissionLevel === 'FULL';

  const startEdit = useCallback((field: string) => {
    if (!canEdit) return false;
    setEditingField(field);
    setError(null);
    return true;
  }, [canEdit]);

  const cancelEdit = useCallback(() => {
    setEditingField(null);
    setError(null);
  }, []);

  const saveField = useCallback(async (saveAction: () => Promise<void>) => {
    if (!canEdit) return false;
    setIsSaving(true);
    setError(null);
    try {
      await saveAction();
      setEditingField(null);
      if (onSave) await onSave();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save changes';
      setError(message);
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [canEdit, onSave]);

  return {
    editingField,
    setEditingField,
    isSaving,
    error,
    canEdit,
    startEdit,
    cancelEdit,
    saveField,
    permissionLevel,
  };
}
