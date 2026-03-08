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
    <div className="mb-4 flex flex-col gap-1">
      {eyebrow ? (
        <span className="text-[11px] uppercase tracking-[0.38em] text-cyan-200/50">
          {eyebrow}
        </span>
      ) : null}
      <h2 className="text-xl font-semibold text-slate-50">{title}</h2>
      {description ? <p className="text-sm text-slate-400">{description}</p> : null}
    </div>
  );
}
