import { useI18n } from "../i18n.jsx";
import { UNIT_CODES } from "../translations.js";

export default function UnitSelect({ value, onChange, ...props }) {
  const { unitLabel } = useI18n();
  return (
    <select className="input" value={value ?? ""} onChange={(e) => onChange(e.target.value)} {...props}>
      {UNIT_CODES.map((code) => (
        <option key={code} value={code}>{unitLabel(code, 1)}</option>
      ))}
    </select>
  );
}
