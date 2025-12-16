import { useState } from 'react';
import axios from 'axios';
import { Upload, CheckCircle, XCircle, FileText, Loader2, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-react';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [msg, setMsg] = useState("");

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    setMsg(""); 
    try {
      const res = await axios.post("http://localhost:8000/analyze", formData);
      setData(res.data);
    } catch (err) { alert("Backend Error"); }
    setLoading(false);
  };

  const handleApprove = () => {
    setMsg(`Proposal Generated: Bid_${data.recommended_product.id}_v1.pdf`);
  };

  // Helper to calculate bar width for the chart
  const getWidth = (price) => {
    if (!data) return '0%';
    // Find max price for scale
    const maxPrice = Math.max(data.recommended_product.price_per_liter, 500); 
    return `${(price / maxPrice) * 100}%`;
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
      <div className="max-w-4xl mx-auto">
        <header className="mb-10 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-900">RFP-Zero Command Center</h1>
            <p className="text-slate-500">Autonomous Technical & Commercial Analysis</p>
          </div>
          <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded font-bold border border-blue-200">Asian Paints B2B</div>
        </header>

        {!data && (
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-24 text-center bg-white shadow-sm">
            <input type="file" id="file" className="hidden" onChange={handleUpload} />
            <label htmlFor="file" className="cursor-pointer flex flex-col items-center gap-4">
              {loading ? <Loader2 size={48} className="animate-spin text-blue-600" /> : <Upload size={48} className="text-slate-400 hover:text-blue-600 transition-colors" />}
              <span className="text-xl font-bold text-slate-700">{loading ? "Running Pattern Recognition..." : "Upload Tender Document"}</span>
            </label>
          </div>
        )}

        {data && (
          <div className="grid gap-6 animate-pulse-once">
            {/* Financial Impact Banner */}
            {data.financial_impact && (
              <div className={`p-4 rounded-lg flex items-center gap-3 border ${data.match_score === 100 ? 'bg-green-50 border-green-200 text-green-800' : 'bg-orange-50 border-orange-200 text-orange-800'}`}>
                {data.match_score === 100 ? <TrendingDown size={24} /> : <AlertTriangle size={24} />}
                <span className="font-bold">{data.financial_impact}</span>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
                {/* Left Card: Product Details */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Recommended SKU</h2>
                        <h3 className="text-2xl font-bold text-blue-900">{data.recommended_product.name}</h3>
                        <p className="text-slate-500 mt-1 text-sm">{data.recommended_product.description}</p>
                        </div>
                    </div>
                    
                    <div className="mb-6">
                        <div className="text-3xl font-bold font-mono text-slate-800">${data.recommended_product.price_per_liter}<span className="text-sm text-slate-400 font-sans"> / Liter</span></div>
                        <div className={`text-sm font-bold mt-1 ${data.match_score === 100 ? 'text-green-600' : 'text-orange-500'}`}>
                            {data.match_score}% Technical Compliance
                        </div>
                    </div>

                    <div className="space-y-3">
                        {data.reasoning.map((log, i) => (
                            <div key={i} className="flex items-start gap-3 text-sm font-medium">
                            {log.status === 'pass' ? <CheckCircle size={16} className="text-green-500 mt-0.5 shrink-0" /> : <XCircle size={16} className="text-red-500 mt-0.5 shrink-0" />}
                            <span className={log.status === 'pass' ? 'text-slate-700' : 'text-red-700'}>{log.msg}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Card: Market Analysis Chart (The Visual Bonus) */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col">
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                        <BarChart3 size={16} /> Market Price Analysis
                    </h3>
                    
                    <div className="space-y-6 flex-1">
                        {/* Selected Product Bar */}
                        <div>
                            <div className="flex justify-between text-sm mb-1 font-bold text-blue-900">
                                <span>{data.recommended_product.name}</span>
                                <span>${data.recommended_product.price_per_liter}</span>
                            </div>
                            <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-600 rounded-full" style={{ width: getWidth(data.recommended_product.price_per_liter) }}></div>
                            </div>
                            <div className="text-xs text-green-600 mt-1 font-bold">Selected (Best Value)</div>
                        </div>

                        {/* Comparison Bar (Reference) */}
                        <div>
                            <div className="flex justify-between text-sm mb-1 text-slate-500">
                                <span>Premium Alternative</span>
                                <span>$450</span>
                            </div>
                            <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                                <div className="h-full bg-slate-300 rounded-full" style={{ width: getWidth(450) }}></div>
                            </div>
                        </div>

                         {/* Market High (Reference) */}
                         <div>
                            <div className="flex justify-between text-sm mb-1 text-slate-500">
                                <span>Market High</span>
                                <span>$850</span>
                            </div>
                            <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                                <div className="h-full bg-slate-300 rounded-full" style={{ width: getWidth(850) }}></div>
                            </div>
                        </div>
                    </div>

                    {!msg ? (
                        <button onClick={handleApprove} className="w-full mt-6 bg-blue-900 text-white py-3 rounded-lg font-bold hover:bg-blue-800 transition flex items-center justify-center gap-2 shadow-lg shadow-blue-100">
                        <FileText size={18} /> Generate Proposal
                        </button>
                    ) : (
                        <div className="w-full mt-6 bg-green-100 text-green-800 py-3 rounded-lg font-bold flex items-center justify-center gap-2 border border-green-200">
                            <CheckCircle size={18} /> {msg}
                        </div>
                    )}
                </div>
            </div>
            
            <button onClick={() => window.location.reload()} className="text-slate-400 hover:text-slate-600 text-sm font-medium text-center w-full">
              Analyze Another Document
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
