import { useEffect, useRef } from 'react';

interface SkipToContentProps {
  targetId?: string;
  label?: string;
  className?: string;
}

export function SkipToContent({
  targetId = 'main-content',
  label = 'Skip to main content',
  className = '',
}: SkipToContentProps) {
  const linkRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab' && !event.shiftKey && linkRef.current) {
        linkRef.current.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      target.setAttribute('tabindex', '-1');
      target.focus();
    }
  };

  const classes = [
    'sr-only',
    'focus:not-sr-only',
    'focus:absolute',
    'focus:top-4',
    'focus:left-4',
    'focus:z-[100]',
    'focus:px-4',
    'focus:py-2',
    'focus:bg-indigo-600',
    'focus:text-white',
    'focus:rounded-lg',
    'focus:shadow-lg',
    'focus:ring-2',
    'focus:ring-indigo-500',
    'focus:ring-offset-2',
    'focus:outline-none',
    'focus:font-semibold',
    className,
  ].join(' ');

  return (
    <a
      ref={linkRef}
      href={"#" + targetId}
      onClick={handleClick}
      className={classes}
      aria-label={label}
    >
      {label}
    </a>
  );
}
