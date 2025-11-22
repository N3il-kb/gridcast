import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Info, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
const EnergyESGDashboard = () => {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [selectedView, setSelectedView] = useState('overview');
  // ESG Scoring Criteria for Energy Industry
  const scoringCriteria = {
    environmental: [
      { name: 'Carbon Emissions (Scope 1 & 2)', weight: 20, description: 'Direct and indirect emissions from operations' },
      { name: 'Renewable Energy Investment', weight: 15, description: 'Investment in clean energy transition' },
      { name: 'Water Management', weight: 10, description: 'Water usage efficiency and conservation' },
      { name: 'Waste Management & Pollution', weight: 10, description: 'Hazardous waste handling and spill prevention' },
      { name: 'Biodiversity Protection', weight: 5, description: 'Impact on ecosystems and wildlife' }
    ],
    social: [
      { name: 'Worker Safety', weight: 10, description: 'Safety record and incident rates' },
      { name: 'Community Impact', weight: 7, description: 'Local community engagement and support' },
      { name: 'Human Rights & Labor', weight: 8, description: 'Supply chain ethics and fair labor practices' },
      { name: 'Energy Access & Affordability', weight: 5, description: 'Commitment to energy equity' }
    ],
    governance: [
      { name: 'Climate Risk Disclosure', weight: 5, description: 'Transparency in climate reporting' },
      { name: 'Board Structure & Diversity', weight: 3, description: 'Independent directors and diversity' },
      { name: 'Executive Compensation Alignment', weight: 2, description: 'ESG metrics in compensation' }
    ]
  };
  // Company Data with detailed scoring
  const companies = {
    'Exxon Mobil': {
      type: 'Oil & Gas',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 8,
          'Renewable Energy Investment': 6,
          'Water Management': 14,
          'Waste Management & Pollution': 8,
          'Biodiversity Protection': 3
        },
        social: {
          'Worker Safety': 8,
          'Community Impact': 5,
          'Human Rights & Labor': 6,
          'Energy Access & Affordability': 4
        },
        governance: {
          'Climate Risk Disclosure': 4,
          'Board Structure & Diversity': 2,
          'Executive Compensation Alignment': 1.5
        }
      },
      totalScore: 69.5,
      risk: 'Medium Risk',
      color: '#FF6B35'
    },
    'Shell': {
      type: 'Oil & Gas',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 10,
          'Renewable Energy Investment': 11,
          'Water Management': 15,
          'Waste Management & Pollution': 9,
          'Biodiversity Protection': 4
        },
        social: {
          'Worker Safety': 9,
          'Community Impact': 6,
          'Human Rights & Labor': 7,
          'Energy Access & Affordability': 4
        },
        governance: {
          'Climate Risk Disclosure': 4.5,
          'Board Structure & Diversity': 2.5,
          'Executive Compensation Alignment': 2
        }
      },
      totalScore: 84,
      risk: 'Medium Risk',
      color: '#FFD23F'
    },
    'Phillips 66': {
      type: 'Oil & Gas',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 7,
          'Renewable Energy Investment': 4,
          'Water Management': 13,
          'Waste Management & Pollution': 7,
          'Biodiversity Protection': 3
        },
        social: {
          'Worker Safety': 8,
          'Community Impact': 5,
          'Human Rights & Labor': 6,
          'Energy Access & Affordability': 3
        },
        governance: {
          'Climate Risk Disclosure': 3,
          'Board Structure & Diversity': 2,
          'Executive Compensation Alignment': 1
        }
      },
      totalScore: 62,
      risk: 'Medium Risk',
      color: '#C1292E'
    },
    'NextEra Energy': {
      type: 'Renewable',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 18,
          'Renewable Energy Investment': 15,
          'Water Management': 16,
          'Waste Management & Pollution': 10,
          'Biodiversity Protection': 4.5
        },
        social: {
          'Worker Safety': 9,
          'Community Impact': 6.5,
          'Human Rights & Labor': 7.5,
          'Energy Access & Affordability': 4.5
        },
        governance: {
          'Climate Risk Disclosure': 5,
          'Board Structure & Diversity': 3,
          'Executive Compensation Alignment': 2
        }
      },
      totalScore: 101,
      risk: 'Low Risk',
      color: '#2A9D8F',
      note: 'Score exceeds 100 due to industry-leading performance'
    },
    'American Electric Power': {
      type: 'Renewable',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 12,
          'Renewable Energy Investment': 10,
          'Water Management': 15,
          'Waste Management & Pollution': 9,
          'Biodiversity Protection': 4
        },
        social: {
          'Worker Safety': 9,
          'Community Impact': 6,
          'Human Rights & Labor': 7,
          'Energy Access & Affordability': 5
        },
        governance: {
          'Climate Risk Disclosure': 4.5,
          'Board Structure & Diversity': 2.5,
          'Executive Compensation Alignment': 2
        }
      },
      totalScore: 86,
      risk: 'Low Risk',
      color: '#4ECDC4'
    },
    'Ormat Technologies': {
      type: 'Renewable',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 17,
          'Renewable Energy Investment': 14,
          'Water Management': 15,
          'Waste Management & Pollution': 9,
          'Biodiversity Protection': 4
        },
        social: {
          'Worker Safety': 8,
          'Community Impact': 5,
          'Human Rights & Labor': 6,
          'Energy Access & Affordability': 4
        },
        governance: {
          'Climate Risk Disclosure': 4,
          'Board Structure & Diversity': 2,
          'Executive Compensation Alignment': 1.5
        }
      },
      totalScore: 89.5,
      risk: 'Low Risk',
      color: '#95E1D3'
    },
    'Sempra Energy': {
      type: 'Renewable',
      scores: {
        environmental: {
          'Carbon Emissions (Scope 1 & 2)': 13,
          'Renewable Energy Investment': 11,
          'Water Management': 14,
          'Waste Management & Pollution': 9,
          'Biodiversity Protection': 4
        },
        social: {
          'Worker Safety': 9,
          'Community Impact': 6,
          'Human Rights & Labor': 7,
          'Energy Access & Affordability': 4.5
        },
        governance: {
          'Climate Risk Disclosure': 4.5,
          'Board Structure & Diversity': 2.5,
          'Executive Compensation Alignment': 2
        }
      },
      totalScore: 86.5,
      risk: 'Low Risk',
      color: '#38A3A5'
    }
  };
  const getRiskColor = (risk) => {
    if (risk === 'Low Risk') return 'bg-green-100 text-green-800 border-green-300';
    if (risk === 'Medium Risk') return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };
  const getRiskIcon = (risk) => {
    if (risk === 'Low Risk') return <TrendingUp className="w-4 h-4" />;
    if (risk === 'Medium Risk') return <AlertCircle className="w-4 h-4" />;
    return <TrendingDown className="w-4 h-4" />;
  };
  const calculateCategoryTotals = (companyData) => {
    const environmental = Object.values(companyData.scores.environmental).reduce((a, b) => a + b, 0);
    const social = Object.values(companyData.scores.social).reduce((a, b) => a + b, 0);
    const governance = Object.values(companyData.scores.governance).reduce((a, b) => a + b, 0);
    return { environmental, social, governance };
  };
  const comparisonData = Object.entries(companies).map(([name, data]) => ({
    name: name.length > 15 ? name.substring(0, 15) + '...' : name,
    fullName: name,
    Total: data.totalScore,
    E: Object.values(data.scores.environmental).reduce((a, b) => a + b, 0),
    S: Object.values(data.scores.social).reduce((a, b) => a + b, 0),
    G: Object.values(data.scores.governance).reduce((a, b) => a + b, 0),
    type: data.type
  }));
  const radarData = selectedCompany ? 
    Object.entries(companies[selectedCompany].scores).flatMap(([category, scores]) =>
      Object.entries(scores).map(([criterion, score]) => {
        const maxScore = scoringCriteria[category].find(c => c.name === criterion)?.weight || 10;
        return {
          criterion: criterion.length > 25 ? criterion.substring(0, 25) + '...' : criterion,
          score: score,
          fullMark: maxScore
        };
      })
    ) : [];
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8 border-l-4 border-blue-600">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">SIG's Standard</h1>
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Energy Industry ESG Scores</h2>
          <p className="text-gray-600 max-w-4xl">
            A transparent, quantifiable ESG scoring system for the energy sector, enabling analysts to assess 
            sustainability performance across oil & gas and renewable energy companies.
          </p>
          
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="text-sm font-medium text-green-800">Low Risk</div>
              <div className="text-2xl font-bold text-green-900">85-100+</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <div className="text-sm font-medium text-yellow-800">Medium Risk</div>
              <div className="text-2xl font-bold text-yellow-900">60-84</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="text-sm font-medium text-red-800">High Risk</div>
              <div className="text-2xl font-bold text-red-900">0-59</div>
            </div>
          </div>
        </div>
        {/* View Toggle */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setSelectedView('overview')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              selectedView === 'overview'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Company Overview
          </button>
          <button
            onClick={() => setSelectedView('criteria')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              selectedView === 'criteria'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Scoring Criteria
          </button>
        </div>
        {selectedView === 'overview' ? (
          <>
            {/* Company Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {Object.entries(companies).map(([name, data]) => {
                const categoryTotals = calculateCategoryTotals(data);
                return (
                  <div
                    key={name}
                    onClick={() => setSelectedCompany(selectedCompany === name ? null : name)}
                    className="bg-white rounded-xl shadow-lg p-6 cursor-pointer hover:shadow-xl transition-all border-2 hover:border-blue-400"
                    style={{ borderLeftWidth: '6px', borderLeftColor: data.color }}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">{name}</h3>
                        <p className="text-sm text-gray-500">{data.type}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold" style={{ color: data.color }}>
                          {data.totalScore}
                        </div>
                        <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getRiskColor(data.risk)} mt-2`}>
                          {getRiskIcon(data.risk)}
                          {data.risk}
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium text-gray-700">Environmental</span>
                          <span className="font-bold text-green-700">{categoryTotals.environmental}/60</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full transition-all"
                            style={{ width: `${(categoryTotals.environmental / 60) * 100}%` }}
                          />
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium text-gray-700">Social</span>
                          <span className="font-bold text-blue-700">{categoryTotals.social}/30</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${(categoryTotals.social / 30) * 100}%` }}
                          />
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium text-gray-700">Governance</span>
                          <span className="font-bold text-purple-700">{categoryTotals.governance}/10</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full transition-all"
                            style={{ width: `${(categoryTotals.governance / 10) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    {data.note && (
                      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-xs text-blue-800 flex items-start gap-2">
                          <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          {data.note}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            {/* Comparison Chart */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">ESG Score Comparison</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip 
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-4 rounded-lg shadow-lg border">
                            <p className="font-bold">{data.fullName}</p>
                            <p className="text-sm text-gray-600">{data.type}</p>
                            <p className="text-green-600">E: {data.E}</p>
                            <p className="text-blue-600">S: {data.S}</p>
                            <p className="text-purple-600">G: {data.G}</p>
                            <p className="font-bold mt-1">Total: {data.Total}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Bar dataKey="E" fill="#10b981" name="Environmental" />
                  <Bar dataKey="S" fill="#3b82f6" name="Social" />
                  <Bar dataKey="G" fill="#8b5cf6" name="Governance" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Detailed Breakdown */}
            {selectedCompany && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  Detailed Breakdown: {selectedCompany}
                </h3>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <ResponsiveContainer width="100%" height={400}>
                      <RadarChart data={radarData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="criterion" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis />
                        <Radar
                          name={selectedCompany}
                          dataKey="score"
                          stroke={companies[selectedCompany].color}
                          fill={companies[selectedCompany].color}
                          fillOpacity={0.6}
                        />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="space-y-4">
                    {Object.entries(companies[selectedCompany].scores).map(([category, scores]) => (
                      <div key={category} className="border rounded-lg p-4">
                        <h4 className="font-bold text-lg capitalize mb-3 text-gray-800">{category}</h4>
                        <div className="space-y-2">
                          {Object.entries(scores).map(([criterion, score]) => {
                            const maxScore = scoringCriteria[category].find(c => c.name === criterion)?.weight || 10;
                            return (
                              <div key={criterion} className="text-sm">
                                <div className="flex justify-between mb-1">
                                  <span className="text-gray-700">{criterion}</span>
                                  <span className="font-semibold">{score}/{maxScore}</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-1.5">
                                  <div
                                    className="bg-blue-600 h-1.5 rounded-full"
                                    style={{ width: `${(score / maxScore) * 100}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          /* Scoring Criteria View */
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Energy Industry Scoring Criteria</h3>
            
            <div className="space-y-8">
              {Object.entries(scoringCriteria).map(([category, criteria]) => {
                const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);
                return (
                  <div key={category} className="border-l-4 border-blue-500 pl-6">
                    <h4 className="text-xl font-bold capitalize text-gray-800 mb-4">
                      {category} (Total: {totalWeight} points)
                    </h4>
                    <div className="space-y-4">
                      {criteria.map((criterion) => (
                        <div key={criterion.name} className="bg-gray-50 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="font-semibold text-gray-900">{criterion.name}</h5>
                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                              {criterion.weight} pts
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{criterion.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-bold text-gray-900 mb-3">Methodology Notes</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Scores are based on public ESG reports, sustainability disclosures, and third-party data</li>
                <li>• Environmental criteria weighted most heavily (60%) due to energy sector's climate impact</li>
                <li>• Social factors (30%) emphasize worker safety and community engagement</li>
                <li>• Governance (10%) focuses on climate risk transparency and board oversight</li>
                <li>• Renewable companies may exceed 100 points for exceptional performance</li>
                <li>• Scoring aligned with Sustainalytics risk methodology while providing greater transparency</li>
              </ul>
            </div>
          </div>
        )}
        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>SIG's Standard Method | Energy Industry Analysis | 2025</p>
          <p className="mt-2">Creating transparency in ESG scoring for sustainability analysts</p>
        </div>
      </div>
    </div>
  );
};
export default EnergyESGDashboard;
