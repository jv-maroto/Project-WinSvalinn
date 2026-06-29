// WinSvalinn — Tauri 2 shell
//
// Opens the WebView and auto-starts the bundled Python FastAPI sidecar
// (winsvalinn-sidecar, declared as bundle.externalBin). The sidecar is killed
// when the main window is destroyed.
//
// In development the PyInstaller binary usually isn't present — the spawn fails
// gracefully and the developer runs `python run_sidecar.py` manually instead.

use std::sync::Mutex;

use tauri::Manager;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Holds the running sidecar child so it can be terminated on shutdown.
struct SidecarProcess(Mutex<Option<CommandChild>>);

fn start_sidecar(app: &tauri::AppHandle) {
    // Kill any leftover sidecar (e.g. from a previous crash) so port 8731 is free
    // and the app never starts up black/dead. CREATE_NO_WINDOW avoids a console flash.
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/IM", "winsvalinn-sidecar.exe"])
            .creation_flags(0x0800_0000)
            .output();
    }

    let sidecar = match app.shell().sidecar("winsvalinn-sidecar") {
        Ok(cmd) => cmd,
        Err(e) => {
            eprintln!(
                "WinSvalinn: sidecar binary not found ({e}). \
                 In development, run `python run_sidecar.py`."
            );
            return;
        }
    };

    match sidecar.spawn() {
        Ok((mut rx, child)) => {
            app.state::<SidecarProcess>().0.lock().unwrap().replace(child);
            // Drain the sidecar's stdout/stderr so its pipe never fills and blocks.
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Terminated(payload) = event {
                        eprintln!("WinSvalinn: sidecar exited ({:?})", payload.code);
                        break;
                    }
                }
            });
        }
        Err(e) => eprintln!(
            "WinSvalinn: failed to spawn sidecar ({e}). \
             In development, run `python run_sidecar.py`."
        ),
    }
}

fn stop_sidecar(app: &tauri::AppHandle) {
    if let Some(child) = app.state::<SidecarProcess>().0.lock().unwrap().take() {
        let _ = child.kill();
    }
    // The PyInstaller onefile sidecar runs a child process (the real uvicorn
    // server) that child.kill() leaves orphaned, holding port 8731 and breaking
    // the next launch ("failed to fetch"). Kill the whole tree by image name.
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/T", "/IM", "winsvalinn-sidecar.exe"])
            .creation_flags(0x0800_0000)
            .output();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Opaque window (transparent:false) + custom decoration-less title bar.
    // The "liquid glass" look is done in the frontend (animated backdrop +
    // backdrop-filter), reliable in WebView2 (native transparency breaks it).
    //
    // Fixed, non-resizable window: the UI is laid out for a single size, so the
    // window is locked to the tauri.conf.json size. No window-state plugin (it
    // would persist an old size and break the layout).
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .manage(SidecarProcess(Mutex::new(None)))
        .setup(|app| {
            start_sidecar(app.handle());
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                stop_sidecar(window.app_handle());
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
