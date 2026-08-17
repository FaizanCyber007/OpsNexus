interface ActionItemChecklistProps {
  items: string[];
}

export function ActionItemChecklist({ items }: ActionItemChecklistProps) {
  return (
    <ul className="flex flex-col gap-2">
      {items.map((item, index) => (
        <li
          key={`${index}-${item}`}
          className="flex items-start gap-2.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white/85"
        >
          <span
            aria-hidden="true"
            className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded-full border border-white/30"
          />
          {item}
        </li>
      ))}
    </ul>
  );
}
