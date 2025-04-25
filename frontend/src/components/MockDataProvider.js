// frontend/src/components/MockDataProvider.js

import React, { createContext, useContext, useState } from 'react';

const MockDataContext = createContext();

// Rename this hook to avoid naming conflicts
export const useMockDataContext = () => useContext(MockDataContext);

export const MockDataProvider = ({ children }) => {
  // Always set mock data to false
  const [mockDataEnabled] = useState(false);
  
  const generateMockScenario = (parameters) => {
    return {
      id: 'mock-scenario-' + Date.now(),
      scenario: {
        network: {
          general: { base_norm_mva: 100 },
          bus: Array(parameters.num_buses || 3).fill().map((_, i) => ({
            uid: `bus_${i}`,
            base_nom_volt: 230,
            initial_status: { vm: 1.0, va: 0.0 }
          })),
          ac_line: Array(parameters.num_buses-1 || 2).fill().map((_, i) => ({
            uid: `acl_${i}`,
            fr_bus: `bus_${i}`,
            to_bus: `bus_${i+1}`,
            r: 0.003,
            x: 0.026
          })),
          simple_dispatchable_device: [
            ...Array(parameters.num_generators || 2).fill().map((_, i) => ({
              uid: `gen_${i}`,
              bus: `bus_${i % parameters.num_buses || 0}`,
              device_type: 'producer',
              initial_status: { p: 0.2 + (i * 0.05), q: 0 }
            })),
            ...Array(parameters.num_loads || 1).fill().map((_, i) => ({
              uid: `load_${i}`,
              bus: `bus_${i % parameters.num_buses || 0}`,
              device_type: 'consumer',
              initial_status: { p: 0.275, q: 0.009 }
            }))
          ]
        }
      },
      message: "Mock scenario generated successfully"
    };
  };
  
  const mockValidateScenario = (scenarioId) => {
    return {
      scenario_id: scenarioId,
      is_valid: true, // Always valid
      physics_validation: {
        is_valid: true,
        voltage_violations: [],
        line_violations: []
      },
      opendss_validation: {
        success: true,
        voltage_violations: [],
        thermal_violations: []
      },
      opendss_success: true
    };
  };
  
  const value = {
    mockDataEnabled,
    setMockDataEnabled: () => {}, // No-op function
    generateMockScenario,
    mockValidateScenario
  };
  
  return (
    <MockDataContext.Provider value={value}>
      {children}
    </MockDataContext.Provider>
  );
};