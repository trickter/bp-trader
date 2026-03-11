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
        <span className="ui-kicker text-[10px] font-semibold text-gray-400">
          {eyebrow}
        </span>
      ) : null}
      <h2 className="font-sans text-base font-semibold tracking-[-0.03em] text-gray-900">{title}</h2>
      {description ? <p className="text-sm leading-6 text-gray-500">{description}</p> : null}
    </div>
  );
}
