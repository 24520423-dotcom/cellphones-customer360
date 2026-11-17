
import { useId } from "react";

export default function Input({
  label,
  type = "text",
  name,
  value,
  onChange,
  placeholder = "",
  required = false,
  disabled = false,
  error,
  helperText,
  className = "",
  id,
  ...props
}) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const errorId = `${inputId}-error`;
  const helperId = `${inputId}-helper`;

  return (
    <div className="w-full">
      {/* Nhãn */}
      {label && (
        <label
          htmlFor={inputId}
          className="mb-2 block text-sm font-medium text-[#171717]"
        >
          {label}
          {required && (
            <span className="ml-1 text-[#D70018]">*</span>
          )}
        </label>
      )}

      {/* Ô nhập */}
      <input
        id={inputId}
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        aria-describedby={
          error ? errorId : helperText ? helperId : undefined
        }
        className={`
          w-full rounded-lg border bg-white px-4 py-2.5
          text-sm text-[#171717] outline-none
          placeholder:text-gray-400
          transition-colors
          focus:border-[#D70018] focus:ring-2 focus:ring-red-100
          disabled:cursor-not-allowed disabled:bg-gray-100
          ${
            error
              ? "border-red-500"
              : "border-gray-300"
          }
          ${className}
        `}
        {...props}
      />

      {/* Thông báo lỗi */}
      {error && (
        <p id={errorId} className="mt-1 text-xs text-[#D70018]">
          {error}
        </p>
      )}

      {/* Hướng dẫn nhập */}
      {!error && helperText && (
        <p id={helperId} className="mt-1 text-xs text-gray-500">
          {helperText}
        </p>
      )}
    </div>
  );
}
