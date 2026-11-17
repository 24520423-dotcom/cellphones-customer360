
export default function Button({
  children,
  variant = "primary",
  size = "md",
  type = "button",
  disabled = false,
  loading = false,
  onClick,
  className = "",
  ...props
}) {
  const variants = {
    primary:
      "bg-[#D70018] text-white hover:bg-[#B50014]",
    secondary:
      "bg-white text-[#171717] border border-gray-300 hover:bg-gray-100",
    outline:
      "bg-white text-[#D70018] border border-[#D70018] hover:bg-red-50",
    danger:
      "bg-[#171717] text-white hover:bg-black",
  };

  const sizes = {
    sm: "px-3 py-2 text-sm",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-lg font-medium transition-colors
        focus-visible:outline-none focus-visible:ring-2
        focus-visible:ring-[#D70018] focus-visible:ring-offset-2
        disabled:cursor-not-allowed disabled:opacity-50
        ${variants[variant] || variants.primary}
        ${sizes[size] || sizes.md}
        ${className}
      `}
      {...props}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
}
