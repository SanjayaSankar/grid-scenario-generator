import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import PropTypes from 'prop-types';
import '../styles/ScenarioVisualization.css';

const ScenarioVisualization = ({ scenario }) => {
  const svgRef = useRef(null);
  
  useEffect(() => {
    if (!scenario || !svgRef.current) return;
    
    // Extract network components
    const network = scenario.network || {};
    const buses = network.bus || [];
    const acLines = network.ac_line|| [];
    const transformers = network.two_winding_transformer || [];
    const devices = network.simple_dispatchable_device || [];
    
    // Setup dimensions and scales
    const svgElement = d3.select(svgRef.current);
    svgElement.selectAll("*").remove();
    
    const width = 800;
    const height = 600;
    const margin = { top: 40, right: 40, bottom: 40, left: 40 };
    
    const svg = svgElement
      .attr("viewBox", `0 0 ${width} ${height}`)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Create a force simulation for automatic layout
    const simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(d => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter((width - margin.left - margin.right) / 2, (height - margin.top - margin.bottom) / 2))
      .force("collision", d3.forceCollide().radius(30));
    
    // Prepare data for visualization
    const nodes = buses.map(bus => {
      const connectedDevices = devices.filter(d => d.bus === bus.uid);
      const generators = connectedDevices.filter(d => d.device_type === 'producer');
      const loads = connectedDevices.filter(d => d.device_type === 'consumer');
      
      return {
        id: bus.uid,
        voltage: bus.initial_status?.vm || 1.0,
        angle: bus.initial_status?.va || 0.0,
        hasGenerator: generators.length > 0,
        hasLoad: loads.length > 0,
        numGenerators: generators.length,
        numLoads: loads.length,
        baseVoltage: bus.base_nom_volt
      };
    });
    
    const links = [];
    
    // Add AC lines
    acLines.forEach(line => {
      if (line.initial_status?.on_status === 1) {
        links.push({
          source: line.fr_bus,
          target: line.to_bus,
          type: "line",
          id: line.uid,
          r: line.r,
          x: line.x,
          limit: line.mva_ub_nom
        });
      }
    });
    
    // Add transformers
    transformers.forEach(xfr => {
      if (xfr.initial_status?.on_status === 1) {
        links.push({
          source: xfr.fr_bus,
          target: xfr.to_bus,
          type: "transformer",
          id: xfr.uid,
          r: xfr.r,
          x: xfr.x
        });
      }
    });
    
    // Create links
    const link = svg.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke-width", 2)
      .attr("class", d => `link ${d.type}`)
      .attr("stroke", d => d.type === "transformer" ? "#6c757d" : "#1E88E5");
    
    // Create nodes
    const node = svg.append("g")
      .attr("class", "nodes")
      .selectAll(".node")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));
    
    // Add bus circles
    node.append("circle")
      .attr("r", d => {
        // Size based on voltage level
        if (d.baseVoltage > 200) return 20;
        if (d.baseVoltage > 100) return 16;
        return 12;
      })
      .attr("fill", d => {
        // Color based on voltage magnitude
        if (d.voltage > 1.05) return "#d32f2f"; // Over voltage - red
        if (d.voltage < 0.95) return "#f57c00"; // Under voltage - orange
        return "#388e3c"; // Normal voltage - green
      })
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 2);
    
    // Add generator symbols
    node.filter(d => d.hasGenerator)
      .append("circle")
      .attr("cx", 0)
      .attr("cy", -8)
      .attr("r", 6)
      .attr("fill", "#ffb300")
      .attr("class", "generator-symbol");
    
    // Add load symbols
    node.filter(d => d.hasLoad)
      .append("rect")
      .attr("x", -6)
      .attr("y", 5)
      .attr("width", 12)
      .attr("height", 6)
      .attr("fill", "#f44336")
      .attr("class", "load-symbol");
    
    // Add bus labels
    node.append("text")
      .attr("dy", d => d.hasGenerator && d.hasLoad ? 24 : (d.hasGenerator || d.hasLoad) ? 20 : 5)
      .attr("text-anchor", "middle")
      .text(d => d.id)
      .attr("class", "bus-label");
    
    // Update simulation nodes and links
    simulation
      .nodes(nodes)
      .on("tick", ticked);
    
    simulation.force("link")
      .links(links);
    
    // Add legends
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${width - margin.left - margin.right - 150}, 10)`);
    
    const legendItems = [
      { label: "Bus", color: "#388e3c", type: "circle" },
      { label: "Generator", color: "#ffb300", type: "circle" },
      { label: "Load", color: "#f44336", type: "rect" },
      { label: "Line", color: "#1E88E5", type: "line" },
      { label: "Transformer", color: "#6c757d", type: "line" }
    ];
    
    legendItems.forEach((item, i) => {
      const lg = legend.append("g")
        .attr("transform", `translate(0, ${i * 20})`);
      
      if (item.type === "circle") {
        lg.append("circle")
          .attr("r", 6)
          .attr("fill", item.color);
      } else if (item.type === "rect") {
        lg.append("rect")
          .attr("x", -6)
          .attr("y", -3)
          .attr("width", 12)
          .attr("height", 6)
          .attr("fill", item.color);
      } else if (item.type === "line") {
        lg.append("line")
          .attr("x1", -10)
          .attr("y1", 0)
          .attr("x2", 10)
          .attr("y2", 0)
          .attr("stroke", item.color)
          .attr("stroke-width", 2);
      }
      
      lg.append("text")
        .attr("x", 15)
        .attr("y", 4)
        .text(item.label)
        .attr("class", "legend-text");
    });
    
    // Add title
    svg.append("text")
      .attr("x", (width - margin.left - margin.right) / 2)
      .attr("y", -20)
      .attr("text-anchor", "middle")
      .attr("class", "chart-title")
      .text(`Network Topology: ${buses.length} Buses, ${acLines.length} Lines`);
    
    // Add zoom capability
    const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        svg.attr("transform", event.transform);
      });
    
    svgElement.call(zoom);
    
    // Simulation tick function
    function ticked() {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
      
      node
        .attr("transform", d => `translate(${d.x},${d.y})`);
    }
    
    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    // Clean up on unmount
    return () => {
      simulation.stop();
    };
  }, [scenario]);
  
  return (
    <div className="scenario-visualization">
      <svg ref={svgRef} className="network-svg" />
    </div>
  );
};

ScenarioVisualization.propTypes = {
  scenario: PropTypes.object.isRequired
};

export default ScenarioVisualization;