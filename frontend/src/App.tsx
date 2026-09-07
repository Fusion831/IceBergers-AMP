import { useState } from 'react';
import { MissionProvider, useMission } from './context/MissionContext';
import { Header } from './components/Header';
import { AntarcticMap } from './components/AntarcticMap';
import { MissionPlanDrawer } from './components/MissionPlanDrawer';
import { RouteDetailsDrawer } from './components/RouteDetailsDrawer';
import { MapLayersMenu } from './components/MapLayersMenu';
import { PathRiskVisualizer } from './components/PathRiskVisualizer';

function MainWorkstation() {
  const {
    routes,
    selectedRouteId,
    setSelectedRouteId,
    selectedRoute,
    timeHorizon,
    setTimeHorizon,
    showH3Grid,
    setShowH3Grid,
    showTrajectories,
    setShowTrajectories
  } = useMission();

  // Drawer / Menu Toggles (HUD panels)
  const [isMissionPlanOpen, setIsMissionPlanOpen] = useState<boolean>(false);
  const [isRouteDetailsOpen, setIsRouteDetailsOpen] = useState<boolean>(false);
  const [isRiskVisualizerOpen, setIsRiskVisualizerOpen] = useState<boolean>(false);
  const [isMapLayersOpen, setIsMapLayersOpen] = useState<boolean>(false);

  // Map Layer States
  const [showIcebergs, setShowIcebergs] = useState<boolean>(true);
  const [basemapStyle, setBasemapStyle] = useState<'google-earth' | 'google-terrain' | 'osm'>('google-earth');
  const [hoveredCellData, setHoveredCellData] = useState<any | null>(null);

  const handleSelectRoute = (routeId: string) => {
    setSelectedRouteId(routeId);
    // Smoothly open the route details drawer when clicked without crashing or unmounting the map
    setIsRouteDetailsOpen(true);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        position: 'relative',
        background: '#090d16'
      }}
    >
      {/* Sleek, Non-technical Header */}
      <Header
        isMissionPlanOpen={isMissionPlanOpen}
        onToggleMissionPlan={() => setIsMissionPlanOpen((prev) => !prev)}
        isRouteDetailsOpen={isRouteDetailsOpen}
        onToggleRouteDetails={() => setIsRouteDetailsOpen((prev) => !prev)}
        isRiskVisualizerOpen={isRiskVisualizerOpen}
        onToggleRiskVisualizer={() => setIsRiskVisualizerOpen((prev) => !prev)}
        isMapLayersOpen={isMapLayersOpen}
        onToggleMapLayers={() => setIsMapLayersOpen((prev) => !prev)}
        selectedRouteName={selectedRoute?.name || 'Fastest Route'}
      />

      {/* Main Map Workspace - Never unmounts */}
      <main
        style={{
          flex: 1,
          width: '100%',
          height: 'calc(100vh - 52px)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <AntarcticMap
          selectedHorizon={timeHorizon}
          selectedRoute={selectedRouteId}
          onHorizonChange={(hz) => setTimeHorizon(hz as any)}
          onSelectRoute={handleSelectRoute}
          showH3Grid={showH3Grid}
          showIcebergs={showIcebergs}
          showTrajectories={showTrajectories}
          basemapStyle={basemapStyle}
          onHoverCell={setHoveredCellData}
        />

        {/* Togglable Left Panel: Mission Plan (First GOL) */}
        <MissionPlanDrawer
          isOpen={isMissionPlanOpen}
          onClose={() => setIsMissionPlanOpen(false)}
        />

        {/* Togglable Right Panel: Route Details */}
        <RouteDetailsDrawer
          isOpen={isRouteDetailsOpen}
          onClose={() => setIsRouteDetailsOpen(false)}
          route={selectedRoute}
          routes={routes}
          onSelectRoute={handleSelectRoute}
          onOpenRiskVisualizer={() => setIsRiskVisualizerOpen(true)}
        />

        {/* Togglable Right Panel: Path Risk Score Visualizer */}
        <PathRiskVisualizer
          isOpen={isRiskVisualizerOpen}
          onClose={() => setIsRiskVisualizerOpen(false)}
          onSelectRoute={handleSelectRoute}
        />

        {/* Togglable Top-Right Panel: Map Layers & Ocean Readout */}
        <MapLayersMenu
          isOpen={isMapLayersOpen}
          onClose={() => setIsMapLayersOpen(false)}
          showH3Grid={showH3Grid}
          onToggleH3Grid={() => setShowH3Grid((prev) => !prev)}
          showIcebergs={showIcebergs}
          onToggleIcebergs={() => setShowIcebergs((prev) => !prev)}
          showTrajectories={showTrajectories}
          onToggleTrajectories={() => setShowTrajectories((prev) => !prev)}
          basemapStyle={basemapStyle}
          onChangeBasemap={setBasemapStyle}
          hoveredCellData={hoveredCellData}
          onOpenRiskVisualizer={() => setIsRiskVisualizerOpen(true)}
        />
      </main>
    </div>
  );
}

export function App() {
  return (
    <MissionProvider>
      <MainWorkstation />
    </MissionProvider>
  );
}

export default App;
