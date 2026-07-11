import { useEffect, useState } from "react";
import { animate, useMotionValue } from "framer-motion";

/** Smoothly counts up to `value` when it changes. */
export function AnimatedNumber({
  value,
  format = (n) => n.toLocaleString("en-US"),
  duration = 0.9,
}: {
  value: number;
  format?: (n: number) => string;
  duration?: number;
}) {
  const mv = useMotionValue(0);
  const [text, setText] = useState(() => format(0));

  useEffect(() => {
    const controls = animate(mv, value, {
      duration,
      ease: "easeOut",
      onUpdate: (v) => setText(format(Math.round(v))),
    });
    return () => controls.stop();
  }, [value, duration, format, mv]);

  return <>{text}</>;
}
