export function SectionTitle({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-5 flex flex-col gap-1">
      {eyebrow ? (
        <span className="text-[10px] font-semibold uppercase tracking-[0.3em] text-gray-400">
          {eyebrow}
        </span>
      ) : null}
      <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      {description ? <p className="text-sm text-gray-500">{description}</p> : null}
    </div>
  );
}
