import { useEffect, useState } from 'react';
import { MissionProvider, useMission } from './context/MissionContext';
import { Header } from './components/Header';
import { MissionSetupView } from './views/MissionSetupView';
import { AntarcticMapView } from './views/AntarcticMapView';
import { EnvironmentalTimelineView } from './views/EnvironmentalTimelineView';
import { LocationComparisonView } from './views/LocationComparisonView';
import { RouteComparisonView } from './views/RouteComparisonView';
import { PredictionInspectorView } from './views/PredictionInspectorView';
import { ViewMode } from './types/mission';

function MainWorkstation() {
  const { activeView, setActiveView } = useMission();
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  // Mouse move listener for smooth cursor-following white and light-blue dynamic gradient
  useEffect(() => {
    let animFrame: number;
    let targetX = 50;
    let targetY = 50;
    let currentX = 50;
    let currentY = 50;

    const handleMouseMove = (e: MouseEvent) => {
      targetX = (e.clientX / window.innerWidth) * 100;
      targetY = (e.clientY / window.innerHeight) * 100;
    };

    const loop = () => {
      // Smooth lerp interpolation for silky motion
      currentX += (targetX - currentX) * 0.15;
      currentY += (targetY - currentY) * 0.15;
      setMousePos({ x: currentX, y: currentY });
      animFrame = requestAnimationFrame(loop);
    };

    window.addEventListener('mousemove', handleMouseMove);
    animFrame = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animFrame);
    };
  }, []);

  // Keyboard shortcut listener (Keys 1-6 switch views)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      const viewMap: Record<string, ViewMode> = {
        '1': 'mission-setup',
        '2': 'antarctic-map',
        '3': 'environmental-timeline',
        '4': 'location-comparison',
        '5': 'route-comparison',
        '6': 'prediction-inspector'
      };
      if (viewMap[e.key]) {
        setActiveView(viewMap[e.key]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setActiveView]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        position: 'relative',
        background: `
          radial-gradient(650px circle at ${mousePos.x}% ${mousePos.y}%, 
            rgba(96, 165, 250, 0.55) 0%, 
            rgba(147, 197, 253, 0.45) 25%, 
            rgba(186, 230, 253, 0.35) 45%, 
            rgba(224, 242, 254, 0.20) 70%, 
            transparent 100%),
          radial-gradient(1200px circle at ${100 - mousePos.x}% ${100 - mousePos.y}%, 
            rgba(186, 230, 253, 0.40) 0%, 
            rgba(224, 242, 254, 0.25) 50%, 
            transparent 80%),
          linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 40%, #ffffff 80%, #dbeafe 100%)
        `
      }}
    >
      {/* Top Bar with Brand and View Navigation */}
      <Header />

      {/* Main View Area */}
      <main style={{ flex: 1, overflow: 'hidden', padding: '10px 14px', position: 'relative', zIndex: 1 }}>
        {activeView === 'mission-setup' && <MissionSetupView />}
        {activeView === 'antarctic-map' && <AntarcticMapView />}
        {activeView === 'environmental-timeline' && <EnvironmentalTimelineView />}
        {activeView === 'location-comparison' && <LocationComparisonView />}
        {activeView === 'route-comparison' && <RouteComparisonView />}
        {activeView === 'prediction-inspector' && <PredictionInspectorView />}
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
