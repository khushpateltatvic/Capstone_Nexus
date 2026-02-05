import {
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Tooltip,
    Legend,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    ScatterChart,
    Scatter,
    ZAxis,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from 'recharts';
import type { TooltipProps } from 'recharts';

// Theme Colors from index.css
const COLORS = {
    primary: '#321a75',
    secondary: '#00c3c4',
    accent: '#faab00',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',
};

const CHART_COLORS = [
    COLORS.primary,
    COLORS.secondary,
    COLORS.accent,
    COLORS.success,
    COLORS.info,
    COLORS.warning,
    COLORS.danger,
];

// Custom Tooltip Wrapper
const CustomTooltip = ({ active, payload, label }: TooltipProps<any, any>) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 rounded-lg shadow-xl border border-gray-100 animate-scale-in">
                <p className="font-semibold text-gray-900 border-b border-gray-50 pb-1 mb-2">{label || payload[0].name}</p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
                        <span>{entry.name}:</span>
                        <span className="font-medium text-gray-900">{entry.value}</span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

// 1. Pie Chart for Distributions
interface PieChartProps {
    data: { name: string; value: number }[];
    height?: number | string;
}

export const NexusPieChart = ({ data, height = 300 }: PieChartProps) => (
    <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                >
                    {data.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                    formatter={(value) => <span className="text-xs text-gray-600 font-medium">{value}</span>}
                />
            </PieChart>
        </ResponsiveContainer>
    </div>
);

// 2. Bar Chart for Comparisons
interface BarChartProps {
    data: { name: string; value: number }[];
    height?: number | string;
    color?: string;
    label?: string;
}

export const NexusBarChart = ({ data, height = 300, color = COLORS.primary, label = 'Value' }: BarChartProps) => (
    <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: '#64748b' }}
                />
                <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: '#64748b' }}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
                <Bar
                    dataKey="value"
                    name={label}
                    fill={color}
                    radius={[4, 4, 0, 0]}
                    barSize={24}
                />
            </BarChart>
        </ResponsiveContainer>
    </div>
);

// 3. Scatter Chart specifically for Stakeholder Matrix
interface StakeholderScatterProps {
    data: {
        name: string;
        alignment: number; // 1-3 (Detractor to Champion)
        influence: number; // 1-3 (Low to High)
        role: string;
    }[];
    height?: number | string;
}

export const StakeholderMatrix = ({ data, height = 350 }: StakeholderScatterProps) => (
    <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                    type="number"
                    dataKey="alignment"
                    name="Alignment"
                    domain={[0.5, 3.5]}
                    ticks={[1, 2, 3]}
                    label={{ value: 'Alignment (Detractor → Champion)', position: 'insideBottom', offset: -10, fontSize: 10 }}
                    tick={{ fontSize: 10 }}
                />
                <YAxis
                    type="number"
                    dataKey="influence"
                    name="Influence"
                    domain={[0.5, 3.5]}
                    ticks={[1, 2, 3]}
                    label={{ value: 'Influence (Low → High)', angle: -90, position: 'insideLeft', fontSize: 10 }}
                    tick={{ fontSize: 10 }}
                />
                <ZAxis type="number" range={[100, 400]} />
                <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                            const p = payload[0].payload;
                            return (
                                <div className="bg-white p-3 rounded-lg shadow-xl border border-gray-100">
                                    <p className="font-bold text-gray-900">{p.name}</p>
                                    <p className="text-xs text-gray-500 mb-2">{p.role}</p>
                                    <div className="space-y-1">
                                        <p className="text-xs flex justify-between gap-4">
                                            <span>Influence:</span>
                                            <span className="font-medium">{p.influence === 3 ? 'High' : p.influence === 2 ? 'Medium' : 'Low'}</span>
                                        </p>
                                        <p className="text-xs flex justify-between gap-4">
                                            <span>Alignment:</span>
                                            <span className="font-medium">{p.alignment === 3 ? 'Champion' : p.alignment === 2 ? 'Neutral' : 'Skeptical'}</span>
                                        </p>
                                    </div>
                                </div>
                            );
                        }
                        return null;
                    }}
                />
                <Scatter
                    name="Stakeholders"
                    data={data}
                    fill={COLORS.secondary}
                    shape="circle"
                    className="animate-pulse-slow"
                />
            </ScatterChart>
        </ResponsiveContainer>
    </div>
);

// 4. Radar Chart for Individual Stakeholder
interface StakeholderRadarProps {
    stakeholder: {
        name: string;
        role: string;
        influence: 'high' | 'medium' | 'low';
        alignment: 'advocate' | 'neutral' | 'skeptical';
    };
    height?: number | string;
}

const getInfluenceValue = (influence: string): number => {
    switch (influence) {
        case 'high': return 100;
        case 'medium': return 66;
        case 'low': return 33;
        default: return 50;
    }
};

const getAlignmentValue = (alignment: string): number => {
    switch (alignment) {
        case 'advocate': return 100;
        case 'neutral': return 50;
        case 'skeptical': return 25;
        default: return 50;
    }
};

export const StakeholderRadar = ({ stakeholder, height = 200 }: StakeholderRadarProps) => {
    const influenceValue = getInfluenceValue(stakeholder.influence);
    const alignmentValue = getAlignmentValue(stakeholder.alignment);
    
    // Calculate derived metrics
    const engagementScore = Math.round((influenceValue + alignmentValue) / 2);
    const riskLevel = stakeholder.alignment === 'skeptical' && stakeholder.influence === 'high' 
        ? 100 
        : stakeholder.alignment === 'skeptical' 
            ? 66 
            : stakeholder.alignment === 'neutral' && stakeholder.influence === 'high'
                ? 50
                : 20;
    const opportunityScore = stakeholder.alignment === 'advocate' 
        ? influenceValue 
        : stakeholder.alignment === 'neutral' 
            ? Math.round(influenceValue * 0.5)
            : 20;

    const radarData = [
        { metric: 'Influence', value: influenceValue, fullMark: 100 },
        { metric: 'Alignment', value: alignmentValue, fullMark: 100 },
        { metric: 'Engagement', value: engagementScore, fullMark: 100 },
        { metric: 'Risk', value: riskLevel, fullMark: 100 },
        { metric: 'Opportunity', value: opportunityScore, fullMark: 100 },
    ];

    const getColor = () => {
        if (stakeholder.alignment === 'advocate') return COLORS.success;
        if (stakeholder.alignment === 'skeptical') return COLORS.danger;
        return COLORS.secondary;
    };

    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis 
                        dataKey="metric" 
                        tick={{ fontSize: 10, fill: '#64748b' }}
                    />
                    <PolarRadiusAxis 
                        angle={90} 
                        domain={[0, 100]} 
                        tick={{ fontSize: 8, fill: '#94a3b8' }}
                        tickCount={4}
                    />
                    <Radar
                        name={stakeholder.name}
                        dataKey="value"
                        stroke={getColor()}
                        fill={getColor()}
                        fillOpacity={0.3}
                        strokeWidth={2}
                    />
                    <Tooltip
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                const p = payload[0].payload;
                                return (
                                    <div className="bg-white p-2 rounded-lg shadow-lg border border-gray-100 text-xs">
                                        <p className="font-semibold text-gray-900">{p.metric}</p>
                                        <p className="text-gray-600">{p.value}%</p>
                                    </div>
                                );
                            }
                            return null;
                        }}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};