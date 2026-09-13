(function () {
    "use strict";

    const DB_NAME = "odental-contingency-v1";
    const STORE_NAME = "encrypted-vault";
    const VAULT_KEY = "primary";
    const META_PREFIX = "odental.contingency.";
    const textEncoder = new TextEncoder();
    const textDecoder = new TextDecoder();
    let cryptoKey = null;
    let vault = null;
    let failedUnlocks = 0;
    let unlockBlockedUntil = 0;

    const byId = (id) => document.getElementById(id);
    const elements = {};

    function bytesToBase64(bytes) {
        let binary = "";
        bytes.forEach((value) => { binary += String.fromCharCode(value); });
        return btoa(binary);
    }

    function base64ToBytes(value) {
        const binary = atob(value);
        return Uint8Array.from(binary, (character) => character.charCodeAt(0));
    }

    function randomBytes(length) {
        return crypto.getRandomValues(new Uint8Array(length));
    }

    function uuid() {
        if (crypto.randomUUID) {
            return crypto.randomUUID();
        }
        const bytes = randomBytes(16);
        bytes[6] = (bytes[6] & 0x0f) | 0x40;
        bytes[8] = (bytes[8] & 0x3f) | 0x80;
        const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
        return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
    }

    async function deriveKey(passphrase, salt) {
        const material = await crypto.subtle.importKey(
            "raw", textEncoder.encode(passphrase), "PBKDF2", false, ["deriveKey"]
        );
        return crypto.subtle.deriveKey(
            {name: "PBKDF2", salt, iterations: 300000, hash: "SHA-256"},
            material,
            {name: "AES-GCM", length: 256},
            false,
            ["encrypt", "decrypt"]
        );
    }

    async function encryptValue(key, value) {
        const iv = randomBytes(12);
        const plaintext = textEncoder.encode(JSON.stringify(value));
        const encrypted = await crypto.subtle.encrypt({name: "AES-GCM", iv}, key, plaintext);
        return {iv: bytesToBase64(iv), data: bytesToBase64(new Uint8Array(encrypted))};
    }

    async function decryptValue(key, encrypted) {
        const plaintext = await crypto.subtle.decrypt(
            {name: "AES-GCM", iv: base64ToBytes(encrypted.iv)},
            key,
            base64ToBytes(encrypted.data)
        );
        return JSON.parse(textDecoder.decode(plaintext));
    }

    function openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, 1);
            request.onupgradeneeded = () => {
                if (!request.result.objectStoreNames.contains(STORE_NAME)) {
                    request.result.createObjectStore(STORE_NAME);
                }
            };
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async function databaseGet() {
        const database = await openDatabase();
        return new Promise((resolve, reject) => {
            const request = database.transaction(STORE_NAME, "readonly")
                .objectStore(STORE_NAME).get(VAULT_KEY);
            request.onsuccess = () => { database.close(); resolve(request.result || null); };
            request.onerror = () => { database.close(); reject(request.error); };
        });
    }

    async function databasePut(value) {
        const database = await openDatabase();
        return new Promise((resolve, reject) => {
            const request = database.transaction(STORE_NAME, "readwrite")
                .objectStore(STORE_NAME).put(value, VAULT_KEY);
            request.onsuccess = () => { database.close(); resolve(); };
            request.onerror = () => { database.close(); reject(request.error); };
        });
    }

    function deleteDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.deleteDatabase(DB_NAME);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
            request.onblocked = () => reject(new Error("Cierre las otras pestañas de contingencia."));
        });
    }

    async function persistVault() {
        if (!cryptoKey || !vault) {
            throw new Error("La bóveda está bloqueada.");
        }
        await databasePut(await encryptValue(cryptoKey, vault));
    }

    function newVault() {
        return {
            schema: 1,
            ownerUserId: null,
            ownerName: "",
            generatedAt: null,
            expiresAt: null,
            appointments: [],
            pendingEntries: [],
        };
    }

    function setMessage(message, isError) {
        elements.appMessage.textContent = message || "";
        elements.appMessage.classList.toggle("hidden", !message);
        elements.appMessage.classList.toggle("error", Boolean(isError));
    }

    function setUnlockMessage(message) {
        elements.unlockMessage.textContent = message || "";
        elements.unlockMessage.classList.toggle("hidden", !message);
    }

    function setBusy(busy) {
        [elements.refreshButton, elements.syncButton, elements.saveEntryButton]
            .forEach((button) => { button.disabled = busy; });
    }

    function formatDate(value) {
        if (!value) return "";
        const date = new Date(value.replace(" ", "T") + "Z");
        if (Number.isNaN(date.getTime())) return value;
        return new Intl.DateTimeFormat("es-HN", {
            dateStyle: "medium", timeStyle: "short"
        }).format(date);
    }

    function entryTypeLabel(value) {
        return {
            clinical_note: "Nota clínica",
            prescription: "Indicación o receta",
            odontogram_finding: "Hallazgo de odontograma",
        }[value] || value;
    }

    function createText(tag, text, className) {
        const element = document.createElement(tag);
        element.textContent = text;
        if (className) element.className = className;
        return element;
    }

    function renderAppointments() {
        const list = elements.appointmentList;
        list.replaceChildren();
        elements.appointmentSelect.replaceChildren(new Option("Seleccione una cita", ""));
        if (!vault.appointments.length) {
            list.append(createText("p", "No hay citas en la copia disponible.", "muted"));
        }
        vault.appointments.forEach((appointment) => {
            const card = document.createElement("div");
            card.className = "appointment";
            card.append(createText("strong", `${formatDate(appointment.start)} · ${appointment.patient_name}`));
            card.append(createText(
                "div",
                `${appointment.service_name} · ${appointment.professional_name} · ${appointment.site_name}`,
                "meta"
            ));
            card.append(createText(
                "div",
                `${appointment.organization_name} · ${appointment.reference}`,
                "meta"
            ));
            list.append(card);
            const label = `${formatDate(appointment.start)} — ${appointment.patient_name} — ${appointment.service_name}`;
            elements.appointmentSelect.add(new Option(label, String(appointment.id)));
        });
        elements.cacheInfo.textContent = vault.generatedAt
            ? `Copia cifrada actualizada ${formatDate(vault.generatedAt)}. Cobertura hasta ${formatDate(vault.expiresAt)}.`
            : "Todavía no se ha descargado la agenda.";
    }

    function renderPending() {
        const list = elements.pendingList;
        list.replaceChildren();
        const pending = vault.pendingEntries || [];
        elements.pendingCount.textContent = `${pending.length} pendiente${pending.length === 1 ? "" : "s"}`;
        if (!pending.length) {
            list.append(createText("p", "No hay anotaciones pendientes.", "muted"));
            return;
        }
        pending.forEach((entry) => {
            const appointment = vault.appointments.find((item) => item.id === entry.appointment_id);
            const card = document.createElement("div");
            card.className = "pending";
            card.append(createText("strong", entryTypeLabel(entry.entry_type)));
            card.append(createText(
                "div",
                appointment ? `${appointment.patient_name} · ${formatDate(appointment.start)}` : `Cita ${entry.appointment_id}`,
                "meta"
            ));
            if (entry.entry_type === "odontogram_finding") {
                card.append(createText("div", `Pieza ${entry.tooth_code} · ${entry.surface} · ${entry.condition}`, "meta"));
            }
            if (entry.content) card.append(createText("p", entry.content));
            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "danger";
            remove.textContent = "Eliminar anotación local";
            remove.addEventListener("click", async () => {
                if (!window.confirm("¿Eliminar esta anotación antes de sincronizarla?")) return;
                vault.pendingEntries = vault.pendingEntries.filter((item) => item.client_uuid !== entry.client_uuid);
                await persistVault();
                renderPending();
            });
            card.append(remove);
            list.append(card);
        });
    }

    function render() {
        renderAppointments();
        renderPending();
        updateConnection();
    }

    function updateConnection() {
        const online = navigator.onLine;
        elements.connectionPill.classList.toggle("online", online);
        elements.connectionText.textContent = online ? "Con conexión" : "Sin conexión";
        elements.refreshButton.disabled = !online;
        elements.syncButton.disabled = !online || !(vault && vault.pendingEntries.length);
    }

    async function rpc(route, params) {
        let response;
        try {
            response = await fetch(route, {
                method: "POST",
                credentials: "same-origin",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({jsonrpc: "2.0", method: "call", params: params || {}, id: uuid()}),
            });
        } catch (error) {
            throw new Error("No hay conexión con O Dental. Los datos continúan cifrados en este dispositivo.");
        }
        const contentType = response.headers.get("content-type") || "";
        if (!response.ok || response.redirected || !contentType.includes("json")) {
            throw new Error("La sesión de O Dental venció. Inicie sesión y vuelva a sincronizar.");
        }
        const payload = await response.json();
        if (payload.error) {
            throw new Error(payload.error.data?.message || payload.error.message || "O Dental rechazó la solicitud.");
        }
        if (!payload.result?.ok) {
            throw new Error(payload.result?.error || "O Dental no pudo completar la solicitud.");
        }
        return payload.result;
    }

    async function refreshAgenda() {
        setBusy(true);
        setMessage("Descargando la agenda autorizada...", false);
        try {
            const result = await rpc("/odental/contingency/bootstrap", {});
            if (vault.ownerUserId && vault.ownerUserId !== result.user_id) {
                throw new Error("Esta bóveda pertenece a otro usuario. Borre los datos locales antes de continuar.");
            }
            vault.ownerUserId = result.user_id;
            vault.ownerName = result.user_name;
            vault.generatedAt = result.generated_at;
            vault.expiresAt = result.expires_at;
            vault.appointments = result.appointments;
            await persistVault();
            render();
            setMessage(`Agenda actualizada para ${result.user_name}.`, false);
        } catch (error) {
            setMessage(error.message, true);
        } finally {
            setBusy(false);
            updateConnection();
        }
    }

    async function saveEntry() {
        const appointmentId = Number(elements.appointmentSelect.value);
        const appointment = vault.appointments.find((item) => item.id === appointmentId);
        const type = elements.entryType.value;
        const content = elements.content.value.trim();
        if (!appointment) {
            setMessage("Seleccione una cita de la agenda disponible.", true);
            return;
        }
        if (type !== "odontogram_finding" && !content) {
            setMessage("Escriba el contenido de la anotación.", true);
            return;
        }
        const entry = {
            client_uuid: uuid(),
            batch_uuid: null,
            organization_id: appointment.organization_id,
            appointment_id: appointment.id,
            entry_type: type,
            content,
            tooth_code: "",
            surface: "",
            condition: "",
            finding_status: "",
            client_created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
        };
        if (type === "odontogram_finding") {
            if (!/^([1-4][1-8]|[5-8][1-5])$/.test(elements.toothCode.value.trim())) {
                setMessage("Ingrese una pieza dental FDI válida, por ejemplo 26.", true);
                return;
            }
            entry.tooth_code = elements.toothCode.value.trim();
            entry.surface = elements.surface.value;
            entry.condition = elements.condition.value;
            entry.finding_status = elements.findingStatus.value;
        }
        vault.pendingEntries.push(entry);
        await persistVault();
        elements.content.value = "";
        elements.toothCode.value = "";
        renderPending();
        updateConnection();
        setMessage("Anotación guardada y cifrada en este dispositivo.", false);
    }

    function pendingGroups() {
        const groups = new Map();
        const newBatchByOrganization = new Map();
        vault.pendingEntries.forEach((entry) => {
            if (!entry.batch_uuid) {
                if (!newBatchByOrganization.has(entry.organization_id)) {
                    newBatchByOrganization.set(entry.organization_id, uuid());
                }
                entry.batch_uuid = newBatchByOrganization.get(entry.organization_id);
            }
            const key = `${entry.organization_id}:${entry.batch_uuid}`;
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(entry);
        });
        return Array.from(groups.values());
    }

    function deviceId() {
        let value = localStorage.getItem(`${META_PREFIX}device`);
        if (!value) {
            value = uuid();
            localStorage.setItem(`${META_PREFIX}device`, value);
        }
        return value;
    }

    async function syncPending() {
        if (!vault.pendingEntries.length) return;
        setBusy(true);
        setMessage("Preparando la sincronización segura...", false);
        try {
            const groups = pendingGroups();
            await persistVault();
            let acceptedTotal = 0;
            for (const entries of groups) {
                const result = await rpc("/odental/contingency/sync", {
                    device_id: deviceId(),
                    batch_uuid: entries[0].batch_uuid,
                    entries: entries.map((entry) => ({
                        client_uuid: entry.client_uuid,
                        appointment_id: entry.appointment_id,
                        entry_type: entry.entry_type,
                        content: entry.content,
                        tooth_code: entry.tooth_code,
                        surface: entry.surface,
                        condition: entry.condition,
                        finding_status: entry.finding_status,
                        client_created_at: entry.client_created_at,
                    })),
                });
                const accepted = new Set(result.accepted_entry_uuids || []);
                acceptedTotal += accepted.size;
                vault.pendingEntries = vault.pendingEntries.filter(
                    (entry) => !accepted.has(entry.client_uuid)
                );
                await persistVault();
                renderPending();
            }
            setMessage(
                `${acceptedTotal} anotación${acceptedTotal === 1 ? "" : "es"} recibida${acceptedTotal === 1 ? "" : "s"}. Quedaron pendientes de revisión en O Dental.`,
                false
            );
        } catch (error) {
            await persistVault();
            setMessage(error.message, true);
        } finally {
            setBusy(false);
            render();
        }
    }

    function lockVault() {
        cryptoKey = null;
        vault = null;
        elements.app.classList.add("hidden");
        elements.unlockCard.classList.remove("hidden");
        elements.passphrase.value = "";
        configureUnlockForm();
    }

    async function eraseLocalData() {
        if (!window.confirm("¿Borrar la agenda y todas las anotaciones no sincronizadas de este dispositivo?")) return;
        cryptoKey = null;
        vault = null;
        await deleteDatabase();
        Object.keys(localStorage)
            .filter((key) => key.startsWith(META_PREFIX))
            .forEach((key) => localStorage.removeItem(key));
        window.location.reload();
    }

    function configureUnlockForm() {
        const configured = Boolean(localStorage.getItem(`${META_PREFIX}verifier`));
        elements.confirmWrap.classList.toggle("hidden", configured);
        elements.unlockTitle.textContent = configured ? "Desbloquear datos locales" : "Proteja los datos de este dispositivo";
        elements.unlockButton.textContent = configured ? "Desbloquear" : "Crear bóveda y continuar";
        elements.passphrase.autocomplete = configured ? "current-password" : "new-password";
        setUnlockMessage("");
    }

    async function unlock() {
        if (Date.now() < unlockBlockedUntil) {
            setUnlockMessage("Espere 30 segundos antes de intentar nuevamente.");
            return;
        }
        const passphrase = elements.passphrase.value;
        const verifierText = localStorage.getItem(`${META_PREFIX}verifier`);
        const configured = Boolean(verifierText);
        if (passphrase.length < 8) {
            setUnlockMessage("La clave local debe tener al menos 8 caracteres.");
            return;
        }
        if (!configured && passphrase !== elements.passphraseConfirm.value) {
            setUnlockMessage("Las claves no coinciden.");
            return;
        }
        elements.unlockButton.disabled = true;
        try {
            let salt;
            if (configured) {
                salt = base64ToBytes(localStorage.getItem(`${META_PREFIX}salt`));
            } else {
                salt = randomBytes(16);
                localStorage.setItem(`${META_PREFIX}salt`, bytesToBase64(salt));
            }
            const candidateKey = await deriveKey(passphrase, salt);
            if (configured) {
                const verifier = await decryptValue(candidateKey, JSON.parse(verifierText));
                if (verifier.marker !== "ODENTAL-CONTINGENCY-V1") throw new Error("Clave incorrecta.");
                const encryptedVault = await databaseGet();
                vault = encryptedVault ? await decryptValue(candidateKey, encryptedVault) : newVault();
            } else {
                localStorage.setItem(
                    `${META_PREFIX}verifier`,
                    JSON.stringify(await encryptValue(candidateKey, {marker: "ODENTAL-CONTINGENCY-V1"}))
                );
                vault = newVault();
            }
            cryptoKey = candidateKey;
            await persistVault();
            failedUnlocks = 0;
            elements.unlockCard.classList.add("hidden");
            elements.app.classList.remove("hidden");
            elements.passphrase.value = "";
            elements.passphraseConfirm.value = "";
            render();
            if (navigator.onLine) await refreshAgenda();
        } catch (error) {
            cryptoKey = null;
            vault = null;
            failedUnlocks += 1;
            if (failedUnlocks >= 5) {
                unlockBlockedUntil = Date.now() + 30000;
                failedUnlocks = 0;
            }
            setUnlockMessage("No se pudo desbloquear. Verifique la clave local.");
        } finally {
            elements.unlockButton.disabled = false;
        }
    }

    async function registerServiceWorker() {
        if (!("serviceWorker" in navigator)) return;
        try {
            const registration = await navigator.serviceWorker.register(
                "/odental/contingency/sw.js", {scope: "/odental/"}
            );
            const worker = registration.active || registration.waiting || registration.installing;
            if (worker) worker.postMessage({type: "CACHE_SHELL"});
        } catch (error) {
            setMessage("Este navegador no pudo preparar el acceso sin internet.", true);
        }
    }

    function initialize() {
        Object.assign(elements, {
            unlockCard: byId("unlockCard"), unlockTitle: byId("unlockTitle"),
            passphrase: byId("passphrase"), passphraseConfirm: byId("passphraseConfirm"),
            confirmWrap: byId("confirmWrap"), unlockButton: byId("unlockButton"),
            unlockMessage: byId("unlockMessage"), app: byId("app"),
            connectionPill: byId("connectionPill"), connectionText: byId("connectionText"),
            pendingCount: byId("pendingCount"), refreshButton: byId("refreshButton"),
            syncButton: byId("syncButton"), lockButton: byId("lockButton"),
            eraseButton: byId("eraseButton"), appMessage: byId("appMessage"),
            cacheInfo: byId("cacheInfo"), appointmentList: byId("appointmentList"),
            appointmentSelect: byId("appointment"), entryType: byId("entryType"),
            dentalFields: byId("dentalFields"), toothCode: byId("toothCode"),
            surface: byId("surface"), condition: byId("condition"),
            findingStatus: byId("findingStatus"), content: byId("content"),
            saveEntryButton: byId("saveEntryButton"), pendingList: byId("pendingList"),
        });
        configureUnlockForm();
        elements.unlockButton.addEventListener("click", unlock);
        elements.passphrase.addEventListener("keydown", (event) => {
            if (event.key === "Enter") unlock();
        });
        elements.entryType.addEventListener("change", () => {
            elements.dentalFields.classList.toggle(
                "hidden", elements.entryType.value !== "odontogram_finding"
            );
        });
        elements.refreshButton.addEventListener("click", refreshAgenda);
        elements.syncButton.addEventListener("click", syncPending);
        elements.saveEntryButton.addEventListener("click", saveEntry);
        elements.lockButton.addEventListener("click", lockVault);
        elements.eraseButton.addEventListener("click", eraseLocalData);
        window.addEventListener("online", updateConnection);
        window.addEventListener("offline", updateConnection);
        updateConnection();
        registerServiceWorker();
    }

    document.addEventListener("DOMContentLoaded", initialize);
})();

