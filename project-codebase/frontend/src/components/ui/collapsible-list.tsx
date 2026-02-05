import { useState } from 'react';
import type { ReactNode } from 'react';
import { Button } from './button';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CollapsibleListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => ReactNode;
  initialDisplayCount?: number;
  maxHeight?: string;
  className?: string;
  itemsClassName?: string;
  showMoreText?: string;
  showLessText?: string;
}

export function CollapsibleList<T>({
  items,
  renderItem,
  initialDisplayCount = 5,
  maxHeight = '400px',
  className = '',
  itemsClassName = '',
  showMoreText,
  showLessText,
}: CollapsibleListProps<T>) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (items.length === 0) {
    return null;
  }

  const shouldShowToggle = items.length > initialDisplayCount;
  const displayItems = !shouldShowToggle || isExpanded 
    ? items 
    : items.slice(0, initialDisplayCount);

  const defaultShowMoreText = showMoreText || `Show all (${items.length})`;
  const defaultShowLessText = showLessText || 'Show less';

  return (
    <div className={cn('space-y-3', className)}>
      <div
        className={cn(
          itemsClassName || 'space-y-2',
          isExpanded && shouldShowToggle && 'overflow-y-auto pr-2 scrollbar-thin'
        )}
        style={isExpanded && shouldShowToggle ? { maxHeight } : undefined}
      >
        {displayItems.map((item, index) => renderItem(item, index))}
      </div>
      
      {shouldShowToggle && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full text-[#321a75] hover:text-[#321a75] hover:bg-[#321a75]/5"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4 mr-2" />
              {defaultShowLessText}
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4 mr-2" />
              {defaultShowMoreText}
            </>
          )}
        </Button>
      )}
    </div>
  );
}
