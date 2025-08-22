export type StatusEvent = {
  step: 'validating' | 'similarity' | 'cache_hit' | 'searching' | 'scraping' | 'summarizing' | 'done' | 'invalid' | 'connected' | 'ping';
  timestamp?: string;
  [key: string]: any;
};

// WebSocket logging utility
const wsLog = {
  info: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.log(`[WS-INFO ${timestamp}] ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    const timestamp = new Date().toISOString();
    console.error(`[WS-ERROR ${timestamp}] ${message}`, error || '');
  },
  debug: (message: string, data?: any) => {
    const timestamp = new Date().toISOString();
    console.debug(`[WS-DEBUG ${timestamp}] ${message}`, data || '');
  }
};

export const connectStatusSocket = (wsId: string, onMessage: (evt: StatusEvent) => void) => {
  const connectionStart = new Date();
  wsLog.info(`Initiating WebSocket connection`, { wsId, url: `ws://localhost:8000/ws/status/${wsId}` });
  
  const ws = new WebSocket(`ws://localhost:8000/ws/status/${wsId}`);
  let messageCount = 0;
  let pingCount = 0;
  
  ws.onopen = () => {
    const connectionTime = (new Date().getTime() - connectionStart.getTime()) / 1000;
    wsLog.info(`WebSocket connection established`, { wsId, connectionTime: `${connectionTime}s`, readyState: ws.readyState });
  };
  
  ws.onmessage = (e) => {
    messageCount++;
    try {
      const data = JSON.parse(e.data);
      
      if (data.step === 'ping') {
        pingCount++;
        wsLog.debug(`Ping received`, { wsId, pingCount, totalMessages: messageCount });
      } else if (data.step === 'connected') {
        wsLog.info(`Connection confirmation received`, { wsId, serverTimestamp: data.timestamp });
      } else {
        wsLog.info(`Pipeline step message received`, { 
          wsId, 
          step: data.step, 
          messageCount, 
          serverTimestamp: data.timestamp,
          dataKeys: Object.keys(data).filter(k => k !== 'step' && k !== 'timestamp')
        });
        onMessage(data as StatusEvent);
      }
    } catch (error) {
      wsLog.error(`Failed to parse WebSocket message`, { wsId, messageCount, rawData: e.data, error });
    }
  };
  
  ws.onerror = (error) => {
    const connectionTime = (new Date().getTime() - connectionStart.getTime()) / 1000;
    wsLog.error(`WebSocket error occurred`, { wsId, connectionTime: `${connectionTime}s`, readyState: ws.readyState, error });
  };
  
  ws.onclose = (event) => {
    const connectionDuration = (new Date().getTime() - connectionStart.getTime()) / 1000;
    wsLog.info(`WebSocket connection closed`, { 
      wsId, 
      code: event.code, 
      reason: event.reason || 'No reason provided', 
      wasClean: event.wasClean,
      connectionDuration: `${connectionDuration}s`,
      totalMessages: messageCount,
      pingsReceived: pingCount
    });
  };
  
  return ws;
};
