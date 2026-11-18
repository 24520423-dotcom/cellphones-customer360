export default function StatusPage({ code, title, children, embedded = false }) {
  return (
    <div className={embedded ? "grid place-items-center p-4" : "grid min-h-dvh place-items-center bg-background p-4"}>
      <section className="crm-card w-full max-w-md text-center">
        <p className="font-bold text-primary">CellphoneS Customer 360</p>
        {code && <p className="mt-4 text-5xl font-bold text-primary sm:text-7xl">{code}</p>}
        <h1 className="mt-4 text-xl font-semibold text-ink">{title}</h1>
        <div className="mt-5">{children}</div>
      </section>
    </div>
  );
}
