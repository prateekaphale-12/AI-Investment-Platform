import { Pie, PieChart, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

const COLORS = ["#6366f1", "#22c55e", "#f97316", "#ec4899", "#eab308", "#38bdf8", "#a855f7"];

type Slice = { name: string; value: number };

export function AllocationPieChart({ data }: { data: Slice[] }) {
  if (!data.length) return <p className="text-sm text-slate-500">No allocation data.</p>;
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <PieChart>
          <Pie dataKey="value" data={data} innerRadius={55} outerRadius={90} paddingAngle={2}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
