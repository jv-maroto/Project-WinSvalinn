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
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Opaque window (transparent:false) + custom decoration-less title bar.
    // The "liquid glass" look is done in the frontend (animated backdrop +
    // backdrop-filter), reliable in WebView2 (native transparency breaks it).
    //
    // window-state plugin: remembers the user's size/position across launches,
    // so the compact default size in tauri.conf.json is only used on first run.
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_window_state::Builder::default().build())
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
