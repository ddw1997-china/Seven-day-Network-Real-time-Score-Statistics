var SeptJSBridge = {
    call(method, params = {}) {
        var message = JSON.stringify({ method, params });
        // iOS
        if (window.webkit?.messageHandlers?.NativeBridge) {
          window.webkit.messageHandlers.NativeBridge.postMessage(message);
        }
        // Android
        else if (window.AndroidBridge?.[method]) {
          window.AndroidBridge[method](JSON.stringify(params));
        } else {
          console.warn('No native bridge available');
        }
      },

    onMessage(payload) {
        var data = typeof payload === 'string' ? JSON.parse(payload) : payload;
        // data :{method:"xx",message:{params:"zzz"}}
        if (data.method) {           
            var evt = new CustomEvent("SeptJSBridageListener", {detail: { action: data.method ,message: data.params },bubbles:true,cancelable:true});
            document.dispatchEvent(evt);
        } 
    }
}

window.SeptJSBridge = SeptJSBridge;
