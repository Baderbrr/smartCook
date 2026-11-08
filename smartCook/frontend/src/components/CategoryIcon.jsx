import { CakeSlice, CupSoda, EggFried, Salad, Sandwich, Soup, Utensils, UtensilsCrossed } from "lucide-react";

const CATEGORY_ICONS = {
  breakfast: EggFried,
  soup: Soup,
  main: UtensilsCrossed,
  supper: Sandwich,
  salad: Salad,
  dessert: CakeSlice,
  drink: CupSoda,
};

export default function CategoryIcon({ category, size = 28 }) {
  const Icon = CATEGORY_ICONS[category] ?? Utensils;
  return <Icon size={size} strokeWidth={1.75} aria-hidden="true" />;
}
