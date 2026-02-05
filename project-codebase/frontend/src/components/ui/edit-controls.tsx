import { Button } from '@/components/ui/button';
import { Pencil, Check, X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EditButtonProps {
  onClick: () => void;
  canEdit: boolean;
  className?: string;
  size?: 'sm' | 'default';
}

export function EditButton({ onClick, canEdit, className, size = 'sm' }: EditButtonProps) {
  if (!canEdit) return null;
  
  return (
    <Button
      variant="ghost"
      size={size === 'sm' ? 'icon' : 'default'}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={cn(
        'h-8 w-8 text-[#321a75] hover:text-white hover:bg-[#321a75] transition-colors',
        className
      )}
      title="Edit"
    >
      <Pencil className="h-4 w-4" />
    </Button>
  );
}

interface EditActionsProps {
  onSave: () => void;
  onCancel: () => void;
  isSaving: boolean;
  className?: string;
}

export function EditActions({ onSave, onCancel, isSaving, className }: EditActionsProps) {
  return (
    <div className={cn('flex items-center gap-1', className)}>
      <Button
        variant="ghost"
        size="icon"
        onClick={(e) => {
          e.stopPropagation();
          onCancel();
        }}
        disabled={isSaving}
        className="h-8 w-8 text-gray-500 hover:text-red-600 hover:bg-red-50"
        title="Cancel"
      >
        <X className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={(e) => {
          e.stopPropagation();
          onSave();
        }}
        disabled={isSaving}
        className="h-8 w-8 text-white bg-[#321a75] hover:bg-[#4a2d99]"
        title="Save"
      >
        {isSaving ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Check className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}

interface InlineEditProps {
  isEditing: boolean;
  canEdit: boolean;
  onStartEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  isSaving: boolean;
  label?: string;
  className?: string;
  children: React.ReactNode;
  editContent: React.ReactNode;
}

export function InlineEdit({
  isEditing,
  canEdit,
  onStartEdit,
  onSave,
  onCancel,
  isSaving,
  label,
  className,
  children,
  editContent,
}: InlineEditProps) {
  return (
    <div className={cn('group relative', className)}>
      {label && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-600">{label}</span>
          {isEditing ? (
            <EditActions onSave={onSave} onCancel={onCancel} isSaving={isSaving} />
          ) : (
            <EditButton onClick={onStartEdit} canEdit={canEdit} />
          )}
        </div>
      )}
      {isEditing ? editContent : children}
      {!label && !isEditing && canEdit && (
        <div className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <EditButton onClick={onStartEdit} canEdit={canEdit} />
        </div>
      )}
    </div>
  );
}
