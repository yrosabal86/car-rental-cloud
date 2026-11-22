import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight, ArrowUpRight, Baby, CalendarCheck, CalendarDays, CarFront,
  Check, ChevronDown, CircleHelp, Fuel, Luggage, LogOut, MapPin, Menu,
  Search, Shield, Sparkles, UserRound, UsersRound, X,
} from "lucide-react";

const RENTAL_API = "/api/rental";
const AUTH_API = "/api/auth";
const TOKEN_KEY = "brisa_access_token";

const CATEGORIES = [
  { id: "", label: "Todos" },
  { id: "economy", label: "Urbano" },
  { id: "compact", label: "Compacto" },
  { id: "suv", label: "SUV" },
  { id: "premium", label: "Premium" },
  { id: "van", label: "Familiar" },
];

const CATEGORY_IMAGES = {
  economy: "photo-1552519507-da3b142c6e3d",
  compact: "photo-1549317661-bd32c8ce0db2",
  suv: "photo-1519641471654-76ce0107ad1b",
  premium: "photo-1616422285623-13ff0162193c",
  van: "photo-1566933293069-b55c7f326dd4",
};

const EXTRA_OPTIONS = [
  { id: "insurance", title: "Protección ampliada", detail: "Viaja con más tranquilidad", price: 12, icon: Shield },
  { id: "gps", title: "GPS", detail: "Encuentra siempre tu camino", price: 5, icon: MapPin },
  { id: "child_seat", title: "Silla infantil", detail: "Seguridad para los más pequeños", price: 4, icon: Baby },
];

const categoryName = (id) => CATEGORIES.find((item) => item.id === id)?.label || id;
const fuelName = (fuel) => ({ gasolina: "Gasolina", diesel: "Diésel", hibrido: "Híbrido", electrico: "Eléctrico" }[fuel] || fuel);
const euro = (amount) => new Intl.NumberFormat("es-ES", {
  style: "currency", currency: "EUR", minimumFractionDigits: 2, maximumFractionDigits: 2,
}).format(Number(amount || 0));

function dateInDays(days = 0) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

async function apiRequest(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("No se pudo conectar con el servidor. Comprueba que Docker esté iniciado y vuelve a intentarlo.");
  }
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (typeof body.detail === "string") throw new Error(body.detail);
    if (Array.isArray(body.detail)) {
      const fields = { full_name: "Nombre y apellidos", birth_date: "Fecha de nacimiento", driver_license: "Permiso de conducir", phone: "Teléfono", email: "Correo electrónico", password: "Contraseña" };
      const messages = body.detail.map((issue) => {
        const field = fields[issue.loc?.at(-1)] || "Formulario";
        let message = String(issue.msg || "Revisa este dato.").replace(/^Value error,\s*/i, "");
        if (issue.type === "missing") message = "Este campo es obligatorio.";
        else if (issue.type === "string_too_short") message = `Debe tener al menos ${issue.ctx?.min_length ?? "los" } caracteres.`;
        else if (issue.type === "string_too_long") message = `No puede superar ${issue.ctx?.max_length ?? "el máximo permitido"} caracteres.`;
        else if (issue.type === "value_error" && field === "Contraseña") message = "Incluye al menos una mayúscula, una minúscula y un número.";
        else if (field === "Correo electrónico") message = "Introduce un correo electrónico válido.";
        else if (field === "Fecha de nacimiento") message = "Introduce una fecha de nacimiento válida.";
        return `${field}: ${message}`;
      });
      throw new Error(messages.join(" "));
    }
    throw new Error("No se pudo completar la solicitud. Comprueba los datos e inténtalo de nuevo.");
  }
  return body;
}

function Dialog({ titleId, children, onClose, wide = false }) {
  return (
    <div className="dialog-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={`dialog-card${wide ? " dialog-wide" : ""}`} role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <button className="dialog-dismiss" onClick={onClose} aria-label="Cerrar"><X size={19} /></button>
        {children}
      </section>
    </div>
  );
}

function Brand({ footer = false }) {
  return (
    <a className={`brand${footer ? " brand-footer" : ""}`} href="#inicio" aria-label="Brisa, inicio">
      <span className="brand-symbol">b</span><span>brisa<span className="brand-period">.</span></span>
    </a>
  );
}

function Header({ loggedIn, userName, onAccount, onBookings, isAdmin, onAdmin }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <header className="topbar">
      <Brand />
      <nav className={`main-nav${menuOpen ? " nav-open" : ""}`} aria-label="Navegación principal">
        <a href="#flota" onClick={() => setMenuOpen(false)}>Encuentra tu coche</a>
        <a href="#como-funciona" onClick={() => setMenuOpen(false)}>Cómo funciona</a>
        <a href="#nosotros" onClick={() => setMenuOpen(false)}>La experiencia Brisa</a>
      </nav>
      <div className="topbar-actions">
        {loggedIn && !isAdmin && <button className="text-action" onClick={onBookings}>Mis viajes</button>}
        {isAdmin && <button className="text-action" onClick={onAdmin}>Administración</button>}
        <button className="account-button" onClick={onAccount}>
          <span className="account-icon"><UserRound size={15} /></span>
          <span>{loggedIn ? userName || "Mi perfil" : "Iniciar sesión"}</span>
        </button>
        <button className="menu-toggle" onClick={() => setMenuOpen((open) => !open)} aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"} aria-expanded={menuOpen}>
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
      </div>
    </header>
  );
}

function SearchPanel({ dates, setDates, onSearch, searching }) {
  const changeStart = (value) => {
    const nextEnd = dates.end <= value ? dateInDaysFrom(value, 1) : dates.end;
    setDates({ start: value, end: nextEnd });
  };
  return (
    <form className="search-panel" onSubmit={onSearch}>
      <div className="search-location search-cell">
        <span className="search-icon"><MapPin size={19} /></span>
        <span className="search-copy"><span className="search-label">LUGAR DE RECOGIDA</span><strong>Málaga, España</strong></span>
        <ChevronDown className="location-chevron" size={15} />
      </div>
      <label className="search-cell date-cell">
        <span className="search-icon"><CalendarDays size={18} /></span>
        <span className="search-copy"><span className="search-label">RECOGIDA</span><input aria-label="Fecha de recogida" type="date" value={dates.start} min={dateInDays()} required onChange={(event) => changeStart(event.target.value)} /></span>
      </label>
      <label className="search-cell date-cell">
        <span className="search-icon"><CalendarDays size={18} /></span>
        <span className="search-copy"><span className="search-label">DEVOLUCIÓN</span><input aria-label="Fecha de devolución" type="date" value={dates.end} min={dateInDaysFrom(dates.start, 1)} required onChange={(event) => setDates((current) => ({ ...current, end: event.target.value }))} /></span>
      </label>
      <button className="primary-button search-submit" type="submit" disabled={searching}>
        <Search size={16} /><span>{searching ? "Buscando…" : "Buscar coches"}</span><ArrowRight size={16} />
      </button>
    </form>
  );
}

function dateInDaysFrom(dateString, days) {
  const date = new Date(`${dateString}T12:00:00`);
  date.setDate(date.getDate() + days);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

function CarCard({ item, onSelect }) {
  const vehicle = item.vehicle;
  const imageId = CATEGORY_IMAGES[vehicle.category] || CATEGORY_IMAGES.compact;
  return (
    <article className="car-card">
      <div className="car-photo-wrap">
        <img className="car-photo" src={vehicle.image_url || `https://images.unsplash.com/${imageId}?auto=format&fit=crop&w=950&q=85`} alt={`${vehicle.brand} ${vehicle.model}`} loading="lazy" onError={(event) => { event.currentTarget.classList.add("image-failed"); }} />
        <span className="category-label">{categoryName(vehicle.category)}</span>
        <span className="car-year">{vehicle.year}</span>
      </div>
      <div className="car-details">
        <div className="car-heading"><div><p className="car-make">{vehicle.brand}</p><h3>{vehicle.model}</h3></div><span className="car-branch"><MapPin size={12} />{vehicle.branch}</span></div>
        <div className="car-feature-line"><span><CalendarCheck size={14} /> {item.nights} {item.nights === 1 ? "día" : "días"}</span><span><Sparkles size={14} /> Precio dinámico</span></div>
        <div className="car-specs"><span><UsersRound size={14} /> {vehicle.seats} plazas</span><span><Fuel size={14} /> {fuelName(vehicle.fuel_type)}</span><span><Luggage size={14} /> {vehicle.luggage_capacity} maletas</span><span>{vehicle.transmission === "automatic" ? "Automático" : "Manual"}</span><span>{vehicle.air_conditioning ? "Aire acondicionado" : "Sin aire acondicionado"}</span></div>
        <div className="availability-note"><Check size={13} /> Disponible en tus fechas</div>
        <div className="car-card-footer"><div className="car-total"><span>Precio total</span><strong>{euro(item.total)}</strong><small>{euro(item.avg_per_night)} / día aprox.</small></div><button className="choose-button" onClick={() => onSelect(item)}>Elegir coche <ArrowRight size={15} /></button></div>
      </div>
    </article>
  );
}

function AuthDialog({ mode, setMode, onClose, onLogin, onRegister, busy, error, success }) {
  const register = mode === "register";
  const handleSubmit = (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    register ? onRegister(values) : onLogin(values);
  };
  return (
    <Dialog titleId="auth-title" onClose={onClose}>
      <div className="dialog-brand"><Brand /></div>
      <span className="eyebrow">TU VIAJE EMPIEZA AQUÍ</span>
      <h2 id="auth-title" className="dialog-title">{register ? "Crea tu cuenta." : "Qué gusto verte."}</h2>
      <p className="dialog-description">{register ? "Unos datos y ya estás más cerca de tu próximo viaje." : "Inicia sesión para gestionar tus reservas."}</p>
      <div className="auth-switch" role="tablist" aria-label="Acceso">
        <button className={!register ? "selected" : ""} role="tab" aria-selected={!register} onClick={() => setMode("login")}>Iniciar sesión</button>
        <button className={register ? "selected" : ""} role="tab" aria-selected={register} onClick={() => setMode("register")}>Crear cuenta</button>
      </div>
      <form className="dialog-form" onSubmit={handleSubmit}>
        {register && <div className="registration-hints"><strong>Antes de crear tu cuenta</strong><span>Nombre: mínimo 2 caracteres.</span><span>Edad: debes tener al menos 21 años.</span><span>Permiso: mínimo 5 caracteres.</span><span>Contraseña: mínimo 8 caracteres, con mayúscula, minúscula y número.</span></div>}
        {register && <>
          <label>Nombre y apellidos<input name="full_name" autoComplete="name" minLength="2" required placeholder="Tu nombre completo" /></label>
          <div className="form-grid-two"><label>Fecha de nacimiento<input name="birth_date" type="date" required max={dateInDaysFrom(dateInDays(), -21 * 365)} /></label><label>Permiso de conducir<input name="driver_license" minLength="5" required placeholder="N.º de permiso" /></label></div>
          <label>Teléfono <span className="optional-label">Opcional</span><input name="phone" autoComplete="tel" placeholder="+34 600 000 000" /></label>
        </>}
        <label>Correo electrónico<input name="email" type="email" autoComplete="email" required placeholder="tu@email.com" /></label>
        <label>Contraseña<input name="password" type="password" autoComplete={register ? "new-password" : "current-password"} required minLength="8" placeholder={register ? "Mayúsculas, minúsculas y números" : "Tu contraseña"} /></label>
        {error && <p className="form-feedback error" role="alert">{error}</p>}
        {success && <p className="form-feedback success" role="status">{success}</p>}
        <button className="primary-button dialog-submit" disabled={busy}>{busy ? "Un momento…" : register ? "Crear mi cuenta" : "Entrar a mi cuenta"}<ArrowRight size={16} /></button>
      </form>
      <p className="privacy-note"><Shield size={13} /> Tus datos se usan únicamente para gestionar tu alquiler.</p>
    </Dialog>
  );
}

function BookingDialog({ item, dates, onClose, onEditDates, onConfirm, busy, error }) {
  const [extras, setExtras] = useState([]);
  const base = Number(item.total);
  const days = Number(item.nights);
  const extrasTotal = EXTRA_OPTIONS.filter((extra) => extras.includes(extra.id)).reduce((sum, extra) => sum + extra.price * days, 0);
  const total = base + extrasTotal;
  const toggle = (id) => setExtras((current) => current.includes(id) ? current.filter((extra) => extra !== id) : [...current, id]);
  const car = item.vehicle;
  return (
    <Dialog titleId="booking-title" onClose={onClose} wide>
      <div className="booking-layout">
        <div className="booking-main">
          <span className="eyebrow">ÚLTIMO PASO</span>
          <h2 id="booking-title" className="dialog-title">Prepara tu viaje.</h2>
          <p className="dialog-description">Añade solo lo que te haga falta. El precio se actualiza al momento.</p>
          <div className="extras-list">
            {EXTRA_OPTIONS.map((extra) => {
              const Icon = extra.icon;
              const checked = extras.includes(extra.id);
              return <label className={`extra-row${checked ? " extra-selected" : ""}`} key={extra.id}>
                <input type="checkbox" checked={checked} onChange={() => toggle(extra.id)} />
                <span className="extra-icon"><Icon size={17} /></span><span className="extra-copy"><strong>{extra.title}</strong><small>{extra.detail}</small></span><span className="extra-price">+{euro(extra.price)}<small> / día</small></span>
              </label>;
            })}
          </div>
          {error && <p className="form-feedback error" role="alert">{error}</p>}
          <button className="primary-button dialog-submit" onClick={() => onConfirm(extras)} disabled={busy}>{busy ? "Confirmando reserva…" : "Confirmar reserva"}<ArrowRight size={16} /></button>
          <p className="terms-note">La reserva se guarda en tu cuenta. El pago se gestiona en el mostrador de recogida.</p>
        </div>
        <aside className="booking-summary">
          <img src={car.image_url || `https://images.unsplash.com/${CATEGORY_IMAGES[car.category] || CATEGORY_IMAGES.compact}?auto=format&fit=crop&w=760&q=82`} alt={`${car.brand} ${car.model}`} />
          <span className="category-label">{categoryName(car.category)}</span>
          <h3>{car.brand} {car.model}</h3>
          <p className="booking-car-specs">{car.year} · {car.seats} plazas · {fuelName(car.fuel_type)} · {car.transmission === "automatic" ? "Automático" : "Manual"}</p>
          <p className="summary-location"><MapPin size={13} /> Recogida en {car.branch}</p>
          <div className="summary-dates"><div><span>Recogida</span><strong>{dates.start}</strong></div><ArrowRight size={15} /><div><span>Devolución</span><strong>{dates.end}</strong></div></div>
          <div className="summary-line"><span>Alquiler · {days} {days === 1 ? "día" : "días"}</span><b>{euro(base)}</b></div>
          {extrasTotal > 0 && <div className="summary-line"><span>Extras seleccionados</span><b>{euro(extrasTotal)}</b></div>}
          <button type="button" className="edit-dates-link" onClick={onEditDates}>Modificar fechas</button>
          <div className="summary-total"><span>Total estimado</span><strong>{euro(total)}</strong></div>
          <p className="summary-tax">Impuestos incluidos · el importe final se confirma al reservar</p>
        </aside>
      </div>
    </Dialog>
  );
}

function TripsDialog({ bookings, loading, error, onClose, onCancel }) {
  return (
    <Dialog titleId="trips-title" onClose={onClose} wide>
      <span className="eyebrow">TU ESPACIO BRISA</span>
      <h2 className="dialog-title" id="trips-title">Mis viajes.</h2>
      <p className="dialog-description">Tus reservas, siempre a mano.</p>
      {loading ? <div className="empty-trips">Cargando tus viajes…</div> : error ? <div className="empty-trips feedback-error">{error}</div> : bookings.length === 0 ? <div className="empty-trips"><CalendarCheck size={25} /><strong>Aún no tienes viajes.</strong><span>Elige tus fechas y encuentra el coche que te lleve más lejos.</span></div> : <div className="trips-list">
        {bookings.map((booking) => <article className="trip-card" key={booking.id}>
          <div><span className={`trip-status status-${booking.status}`}>{({confirmed:"Confirmada",active:"Vehículo entregado",completed:"Vehículo devuelto",cancelled:"Cancelada",needs_reassignment:"Pendiente de reasignación"})[booking.status] || booking.status}</span><h3>Reserva BR-{String(booking.id).padStart(5, "0")}</h3><p>{booking.start_date} <ArrowRight size={13} /> {booking.end_date}</p></div>
          <div className="trip-total"><strong>{euro(booking.quoted_total)}</strong>{booking.status === "confirmed" && (booking.start_date <= dateInDays(1) ? <span className="cancel-closed">Cancelación cerrada: menos de 24 h</span> : <button className="cancel-link" onClick={() => onCancel(booking.id)}>Cancelar viaje</button>)}</div>
        </article>)}
      </div>}
    </Dialog>
  );
}

function ProfileDialog({ profile, onClose, onLogout }) {
  return <Dialog titleId="profile-title" onClose={onClose}>
    <span className="eyebrow">TU CUENTA</span><h2 className="dialog-title" id="profile-title">Mi perfil.</h2>
    {profile ? <div className="profile-fields"><div><span>Nombre</span><strong>{profile.full_name}</strong></div><div><span>Correo electrónico</span><strong>{profile.email}</strong></div><div><span>Teléfono</span><strong>{profile.phone || "No indicado"}</strong></div><div><span>Tipo de cuenta</span><strong>Cliente</strong></div></div> : <p className="dialog-description">Cargando tu perfil…</p>}
    <button className="secondary-button profile-logout" onClick={onLogout}><LogOut size={15} /> Cerrar sesión</button>
  </Dialog>;
}

const ADMIN_HEADERS = (token) => ({ Authorization: `Bearer ${token}` });
const blankVehicle = { plate:"", brand:"", model:"", year:new Date().getFullYear(), category:"compact", base_daily_rate:"", mileage:0, branch:"Málaga", seats:5, transmission:"manual", fuel_type:"gasolina", luggage_capacity:2, air_conditioning:true, image_url:"" };
function AdminDialog({ token, onClose, notify }) {
  const [tab, setTab] = useState("reservas");
  const [users, setUsers] = useState([]); const [reservations, setReservations] = useState([]); const [vehicles, setVehicles] = useState([]); const [rentals, setRentals] = useState([]);
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const [editing, setEditing] = useState(null); const [vehicleForm, setVehicleForm] = useState(blankVehicle);
  const reload = async () => {
    setError("");
    try {
      const [u, r, v, activeRentals] = await Promise.all([
        apiRequest(`${AUTH_API}/admin/users?role=customer`, {headers: ADMIN_HEADERS(token)}),
        apiRequest(`${RENTAL_API}/reservations`, {headers: ADMIN_HEADERS(token)}),
        apiRequest(`${RENTAL_API}/fleet/vehicles`, {headers: ADMIN_HEADERS(token)}),
        apiRequest(`${RENTAL_API}/rentals`, {headers: ADMIN_HEADERS(token)}),
      ]);
      setUsers(u); setReservations(r); setVehicles(v); setRentals(activeRentals);
    } catch (e) { setError(e.message); }
  };
  useEffect(() => { reload(); }, []);
  const act = async (url, options, success) => { setBusy(true); setError(""); try { await apiRequest(url, {...options, headers:{...ADMIN_HEADERS(token), ...(options?.headers||{})}}); await reload(); notify(success); } catch(e) { setError(e.message); } finally { setBusy(false); } };
  const pickup = (id) => act(`${RENTAL_API}/rentals/pickup`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({reservation_id:id})}, `Recogida registrada · BR-${String(id).padStart(5,"0")}`);
  const returnCar = (rentalId, reservationId) => { const mileage = window.prompt("Kilometraje final del coche:"); if (mileage === null) return; const value = Number(mileage); if (!Number.isInteger(value) || value < 0) { setError("Introduce un kilometraje válido."); return; } act(`${RENTAL_API}/rentals/${rentalId}/return`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({end_mileage:value})}, `Devolución registrada · BR-${String(reservationId).padStart(5,"0")}`); };
  const saveVehicle = (event) => { event.preventDefault(); const data = {...vehicleForm, year:Number(vehicleForm.year), mileage:Number(vehicleForm.mileage), seats:Number(vehicleForm.seats), luggage_capacity:Number(vehicleForm.luggage_capacity), air_conditioning:Boolean(vehicleForm.air_conditioning), image_url:vehicleForm.image_url || null}; act(editing ? `${RENTAL_API}/fleet/vehicles/${editing}` : `${RENTAL_API}/fleet/vehicles`, {method:editing?"PUT":"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)}, editing ? "Vehículo actualizado" : "Vehículo añadido"); setEditing(null); setVehicleForm(blankVehicle); };
  const startEdit = (v) => {setEditing(v.id); setVehicleForm({...v, base_daily_rate:String(v.base_daily_rate), image_url:v.image_url||""});};
  return <Dialog titleId="admin-title" onClose={onClose} wide><span className="eyebrow">BRISA · OPERACIONES</span><h2 className="dialog-title" id="admin-title">Administración.</h2><div className="admin-tabs">{[["reservas","Reservas y alquileres"],["clientes","Clientes"],["flota","Flota"]].map(([id,label])=><button key={id} className={tab===id?"selected":""} onClick={()=>setTab(id)}>{label}</button>)}</div>{error&&<p className="form-feedback error" role="alert">{error}</p>}
    {tab==="reservas"&&<div className="admin-list">{reservations.length===0?<p className="dialog-description">Todavía no hay reservas.</p>:reservations.map(r=>{const car=vehicles.find(v=>v.id===r.vehicle_id);const customer=users.find(u=>u.id===r.customer_id);const rental=rentals.find(item=>item.reservation_id===r.id);return <article className="admin-row" key={r.id}><div><b>BR-{String(r.id).padStart(5,"0")} · {car?`${car.brand} ${car.model}`:`Coche ${r.vehicle_id}`}</b><span>{customer?.full_name||`Cliente ${r.customer_id}`} · {customer?.email||""}</span><span>{r.start_date} → {r.end_date} · {euro(r.quoted_total)} · {r.status}</span></div>{r.status==="confirmed"&&<button disabled={busy} className="choose-button" onClick={()=>pickup(r.id)}>Registrar recogida</button>}{r.status==="active"&&rental&&<button disabled={busy} className="choose-button" onClick={()=>returnCar(rental.id,r.id)}>Registrar devolución</button>}</article>})}</div>}
    {tab==="clientes"&&<div className="admin-list">{users.map(u=><article className="admin-row" key={u.id}><div><b>{u.full_name}</b><span>{u.email} · {u.phone||"Sin teléfono"}</span><span>Nacimiento: {u.birth_date||"—"} · Permiso: {u.driver_license||"—"} · {u.is_active?"Activo":"Desactivado"}</span></div><button className="secondary-button" disabled={busy} onClick={()=>act(`${AUTH_API}/admin/users/${u.id}/status`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({is_active:!u.is_active})},u.is_active?"Cuenta desactivada":"Cuenta reactivada")}>{u.is_active?"Dar de baja":"Reactivar"}</button></article>)}</div>}
    {tab==="flota"&&<><form className="admin-vehicle-form" onSubmit={saveVehicle}><strong>{editing?"Modificar coche":"Añadir coche"}</strong><div className="admin-vehicle-grid">{[["plate","Matrícula"],["brand","Marca"],["model","Modelo"],["year","Año"],["base_daily_rate","Precio base / día"],["mileage","Kilometraje"],["branch","Oficina"],["seats","Plazas"],["luggage_capacity","Maletas"],["image_url","URL de la foto"]].map(([key,label])=><label key={key}>{label}<input required={key!=="image_url"} type={key==="year"||key==="mileage"||key==="seats"||key==="luggage_capacity"?"number":"text"} value={vehicleForm[key]??""} onChange={e=>setVehicleForm({...vehicleForm,[key]:e.target.value})}/></label>)}<label>Categoría<select value={vehicleForm.category} onChange={e=>setVehicleForm({...vehicleForm,category:e.target.value})}>{CATEGORIES.filter(c=>c.id).map(c=><option value={c.id} key={c.id}>{c.label}</option>)}</select></label><label>Combustible<select value={vehicleForm.fuel_type} onChange={e=>setVehicleForm({...vehicleForm,fuel_type:e.target.value})}>{["gasolina","diesel","hibrido","electrico"].map(x=><option key={x}>{x}</option>)}</select></label></div><div className="admin-form-actions"><button className="choose-button" disabled={busy}>{editing?"Guardar cambios":"Añadir coche"}</button>{editing&&<button type="button" className="secondary-button" onClick={()=>{setEditing(null);setVehicleForm(blankVehicle)}}>Cancelar</button>}</div></form><div className="admin-list">{vehicles.map(v=><article className="admin-row" key={v.id}><div><b>{v.brand} {v.model} · {v.plate}</b><span>{categoryName(v.category)} · {euro(v.base_daily_rate)}/día · {v.status}</span></div><div className="admin-form-actions"><button className="secondary-button" onClick={()=>startEdit(v)}>Modificar</button>{v.status==="maintenance"&&<button className="secondary-button" disabled={busy} onClick={()=>act(`${RENTAL_API}/fleet/vehicles/${v.id}/activate`,{method:"POST"},"Coche disponible para reservar")}>Marcar disponible</button>}{v.status==="available"&&<button className="secondary-button" disabled={busy} onClick={()=>act(`${RENTAL_API}/fleet/vehicles/${v.id}/maintenance`,{method:"POST"},"Coche enviado a mantenimiento")}>Enviar a mantenimiento</button>}</div></article>)}</div></>}
    <button className="secondary-button" onClick={reload}>Actualizar datos</button></Dialog>;
}

function HelpDialog({ onClose }) {
  return <Dialog titleId="help-title" onClose={onClose} wide>
    <span className="eyebrow">AYUDA</span><h2 className="dialog-title" id="help-title">Antes de salir a la carretera.</h2>
    <div className="help-list">
      <article><h3>¿Cómo sé si un coche está libre?</h3><p>El catálogo solo muestra coches disponibles para todas las fechas elegidas. La disponibilidad se comprueba otra vez al confirmar.</p></article>
      <article><h3>¿Son exactas las prestaciones?</h3><p>La flota incluida es de demostración. Sus fichas muestran datos de ejemplo; confirma la versión y el equipamiento de la unidad en la oficina.</p></article>
      <article><h3>¿Cuánto dura el alquiler?</h3><p>Puedes alquilar desde una noche. El buscador propone cuatro noches como ejemplo, pero puedes cambiar la recogida y la devolución antes de buscar.</p></article>
      <article><h3>¿Cuándo y dónde pago?</h3><p>El pago se realiza en la oficina al recoger el vehículo. El precio estimado aparece antes de confirmar la reserva.</p></article>
      <article><h3>¿Recibiré un correo?</h3><p>Por ahora no hay envío de correos configurado. La reserva confirmada y su localizador aparecen en «Mis viajes».</p></article>
    </div>
    <button className="secondary-button" onClick={onClose}>Entendido</button>
  </Dialog>;
}

function TermsDialog({ onClose }) {
  return <Dialog titleId="terms-title" onClose={onClose} wide>
    <span className="eyebrow">CONDICIONES DE RESERVA</span><h2 className="dialog-title" id="terms-title">Claro desde el principio.</h2>
    <div className="help-list">
      <article><h3>Duración y disponibilidad</h3><p>La estancia mínima es de una noche y la máxima de 30 días. La disponibilidad corresponde al rango completo de fechas y se vuelve a validar al reservar.</p></article>
      <article><h3>Pago</h3><p>El pago se realiza en la oficina donde se recoge el coche. El precio mostrado es estimado y se confirma al finalizar la reserva.</p></article>
      <article><h3>Cancelación</h3><p>Con 7 o más días de antelación no hay penalización; entre 3 y 6 días se retiene el 25 %; entre 24 y 48 horas, el 50 %. No se puede cancelar durante las 24 horas previas.</p><small>Las reservas usan fechas de calendario; por eso la aplicación cierra la cancelación desde el día anterior al inicio.</small></article>
      <article><h3>Confirmación</h3><p>La reserva se confirma en pantalla y queda guardada en «Mis viajes». Actualmente no se envía correo de confirmación.</p></article>
    </div>
    <button className="secondary-button" onClick={onClose}>Cerrar</button>
  </Dialog>;
}

function dateText(iso) {
  if (!iso) return "";
  return new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${iso}T12:00:00`));
}

export default function App() {
  const [dates, setDates] = useState({ start: dateInDays(1), end: dateInDays(5) });
  const [category, setCategory] = useState("");
  const [cars, setCars] = useState([]);
  const [loadingCars, setLoadingCars] = useState(true);
  const [searchError, setSearchError] = useState("");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [profile, setProfile] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [selectedCar, setSelectedCar] = useState(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [bookingBusy, setBookingBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  const [bookingError, setBookingError] = useState("");
  const [bookings, setBookings] = useState([]);
  const [loadingBookings, setLoadingBookings] = useState(false);
  const [bookingsError, setBookingsError] = useState("");
  const [toast, setToast] = useState("");

  const loadCars = useCallback(async (nextCategory = category, nextDates = dates) => {
    if (!nextDates.start || !nextDates.end || nextDates.end <= nextDates.start) {
      setSearchError("La fecha de devolución debe ser posterior a la recogida.");
      return;
    }
    setLoadingCars(true);
    setSearchError("");
    try {
      const query = new URLSearchParams({ start_date: nextDates.start, end_date: nextDates.end });
      if (nextCategory) query.set("category", nextCategory);
      const result = await apiRequest(`${RENTAL_API}/availability?${query}`);
      setCars(result);
    } catch (error) {
      setSearchError(error.message || "No se pudo conectar con el servicio de alquiler.");
      setCars([]);
    } finally {
      setLoadingCars(false);
    }
  }, [category, dates]);

  useEffect(() => { loadCars(); }, []); // carga inicial para enseñar disponibilidad nada más abrir la web

  useEffect(() => {
    if (!token) { setProfile(null); return; }
    apiRequest(`${AUTH_API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(setProfile)
      .catch(() => { localStorage.removeItem(TOKEN_KEY); setToken(null); });
  }, [token]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(""), 4200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const nights = useMemo(() => {
    if (!dates.start || !dates.end) return 0;
    return Math.max(0, Math.round((new Date(`${dates.end}T12:00:00`) - new Date(`${dates.start}T12:00:00`)) / 86_400_000));
  }, [dates]);

  const onSearch = (event) => {
    event.preventDefault();
    loadCars(category, dates);
    document.querySelector("#flota")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const chooseCategory = (value) => {
    setCategory(value);
    loadCars(value, dates);
  };

  const openAuth = () => {
    setAuthMode("login"); setAuthError(""); setAuthSuccess(""); setDialog("auth");
  };

  const handleLogin = async (values) => {
    setAuthBusy(true); setAuthError("");
    try {
      const credentials = new URLSearchParams({ username: values.email, password: values.password });
      const session = await apiRequest(`${AUTH_API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: credentials });
      localStorage.setItem(TOKEN_KEY, session.access_token);
      setToken(session.access_token); setDialog(null); setToast("¡Qué bien tenerte de vuelta!");
      if (selectedCar) setDialog("booking");
    } catch (error) { setAuthError(error.message); }
    finally { setAuthBusy(false); }
  };

  const handleRegister = async (values) => {
    setAuthBusy(true); setAuthError(""); setAuthSuccess("");
    try {
      await apiRequest(`${AUTH_API}/auth/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
        full_name: values.full_name, email: values.email, password: values.password,
        birth_date: values.birth_date, driver_license: values.driver_license, phone: values.phone || null,
      }) });
      setAuthMode("login"); setAuthSuccess("Tu cuenta está lista. Inicia sesión para seguir con la reserva.");
    } catch (error) { setAuthError(error.message); }
    finally { setAuthBusy(false); }
  };

  const selectCar = (item) => {
    setSelectedCar(item); setBookingError("");
    if (!token) { openAuth(); return; }
    setDialog("booking");
  };

  const confirmBooking = async (extras) => {
    setBookingBusy(true); setBookingError("");
    try {
      const booking = await apiRequest(`${RENTAL_API}/reservations`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ vehicle_id: selectedCar.vehicle.id, start_date: dates.start, end_date: dates.end, extras }) });
      setDialog(null); setSelectedCar(null); setToast(`Reserva confirmada · localizador BR-${String(booking.id).padStart(5, "0")}`);
      await loadCars(category, dates);
    } catch (error) { setBookingError(error.message); }
    finally { setBookingBusy(false); }
  };

  const openBookings = async () => {
    setDialog("trips"); setLoadingBookings(true); setBookingsError("");
    try { setBookings(await apiRequest(`${RENTAL_API}/reservations/me`, { headers: { Authorization: `Bearer ${token}` } })); }
    catch (error) { setBookingsError(error.message); }
    finally { setLoadingBookings(false); }
  };

  const openProfile = () => setDialog("profile");
  const openAdmin = () => setDialog("admin");
  const editBookingDates = () => {
    setDialog(null);
    window.setTimeout(() => document.querySelector(".search-section")?.scrollIntoView({ behavior: "smooth", block: "center" }), 0);
  };

  const cancelBooking = async (id) => {
    if (!window.confirm("¿Quieres cancelar esta reserva? Se aplicará la política de cancelación correspondiente.")) return;
    try {
      const result = await apiRequest(`${RENTAL_API}/reservations/${id}/cancel`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      setToast(`Reserva cancelada · reembolso estimado ${euro(result.refund)}`);
      setBookings((current) => current.map((booking) => booking.id === id ? { ...booking, status: "cancelled" } : booking));
      await loadCars(category, dates);
    } catch (error) { setBookingsError(error.message); }
  };

  const signOut = () => {
    localStorage.removeItem(TOKEN_KEY); setToken(null); setDialog(null); setToast("Sesión cerrada. ¡Hasta pronto!");
  };

  const selectDates = (value, field) => {
    if (field === "start") setDates((current) => ({ start: value, end: current.end <= value ? dateInDaysFrom(value, 1) : current.end }));
    else setDates((current) => ({ ...current, end: value }));
  };

  return <>
    <Header loggedIn={Boolean(token)} userName={profile?.full_name?.split(" ")[0]} onAccount={token ? openProfile : openAuth} onBookings={openBookings} isAdmin={profile?.role === "admin"} onAdmin={openAdmin} />
    <main>
      <section className="hero-section" id="inicio">
        <div className="hero-copy">
          <span className="eyebrow"><i /> ALQUILER DE COCHES, A TU MANERA</span>
          <h1>Tu próximo viaje<br />empieza <em>por aquí.</em></h1>
          <p>Elige tu destino. Encuentra el coche que va contigo. Lo demás es carretera.</p>
          <div className="hero-reassurance"><span><Check size={14} /> Precio claro</span><span><Check size={14} /> Reserva flexible</span></div>
        </div>
        <div className="hero-visual">
          <div className="hero-image" role="img" aria-label="Coche listo para empezar el viaje" />
          <div className="hero-image-shade" />
          <div className="hero-location"><MapPin size={14} /><span>MÁLAGA, ESPAÑA</span></div>
          <div className="hero-photo-note"><span className="note-mark">b.</span><span>Encuentra tu<br /><strong>propio camino.</strong></span></div>
          <span className="hero-counter">01 <i /> 03</span>
        </div>
        <div className="hero-ornament" aria-hidden="true">✳</div>
      </section>

      <section className="search-section" aria-label="Buscar coches disponibles">
        <SearchPanel dates={dates} setDates={setDates} onSearch={onSearch} searching={loadingCars} />
        <p className="search-assurance"><Shield size={13} /> Desde 1 noche · fechas flexibles · precio total antes de reservar.</p>
      </section>

      <section className="intro-section page-shell" id="nosotros">
        <div className="intro-title"><span className="eyebrow"><i /> VIAJAR DEBERÍA SER SENCILLO</span><h2>Más camino.<br /><em>Menos vueltas.</em></h2></div>
        <div className="intro-description"><p>Un fin de semana improvisado o esas vacaciones que llevas esperando. En Brisa tienes un coche listo para acompañarte.</p><a className="inline-link" href="#como-funciona">Así de fácil funciona <ArrowUpRight size={15} /></a></div>
        <div className="intro-numbers"><div><strong>01</strong><span>Eliges fechas</span></div><div><strong>02</strong><span>Encuentras tu coche</span></div><div><strong>03</strong><span>Empieza el viaje</span></div></div>
      </section>

      <section className="fleet-section" id="flota">
        <div className="page-shell">
          <div className="fleet-heading"><div><span className="eyebrow"><i /> PARA CADA FORMA DE VIAJAR</span><h2>La flota <em>Brisa.</em></h2></div><div className="fleet-heading-copy"><p>Disponibles en Málaga para tus fechas.</p><span><span className="live-dot" /> Actualizado al momento</span></div></div>
          <div className="fleet-toolbar"><div className="category-list" role="group" aria-label="Filtrar coches por categoría">{CATEGORIES.map((item) => <button key={item.id || "all"} className={`category-filter${category === item.id ? " active" : ""}`} onClick={() => chooseCategory(item.id)} aria-pressed={category === item.id}>{item.label}</button>)}</div><span className="dates-summary"><CalendarDays size={14} /> {dateText(dates.start)} — {dateText(dates.end)}</span></div>
          {searchError ? <div className="fleet-state error-state"><div className="state-icon"><CircleHelp size={23} /></div><h3>No pudimos cargar los coches.</h3><p>{searchError}</p><button className="secondary-button" onClick={() => loadCars(category, dates)}>Volver a intentar <ArrowRight size={15} /></button></div> : loadingCars && !cars.length ? <div className="fleet-state"><div className="loading-spinner" /><p>Buscando coches disponibles…</p></div> : cars.length ? <>
            <div className="fleet-grid">{cars.map((item) => <CarCard key={item.vehicle.id} item={item} onSelect={selectCar} />)}</div>
            <div className="fleet-footnote"><span><Shield size={14} /></span> Precios calculados para tus fechas · Impuestos incluidos · Extras opcionales</div>
          </> : <div className="fleet-state"><div className="state-icon"><CarFront size={25} /></div><h3>No hay coches disponibles para estas fechas.</h3><p>Prueba con otras fechas o selecciona otra categoría. Te ayudamos a encontrar una alternativa.</p><button className="secondary-button" onClick={() => { setCategory(""); loadCars("", dates); }}>Ver toda la flota <ArrowRight size={15} /></button></div>}
        </div>
      </section>

      <section className="experience-section page-shell" id="como-funciona">
        <div className="experience-image-wrap"><div className="experience-image" role="img" aria-label="Paisaje verde en una ruta de viaje" /><div className="experience-label"><Sparkles size={15} /><span>CAMBIA DE AIRE</span></div></div>
        <div className="experience-copy"><span className="eyebrow eyebrow-light"><i /> TU VIAJE, SIN COMPLICACIONES</span><h2>De la idea<br />a la <em>carretera.</em></h2><p>Reserva desde casa con las fechas claras y el precio por delante. Tú decides cuándo, nosotros ponemos el coche.</p><a className="light-button" href="#flota">Encuentra tu coche <ArrowRight size={15} /></a><div className="signature">Nos vemos en el camino. <span>— Brisa</span></div></div>
      </section>

      <section className="steps-section page-shell">
        <div className="steps-header"><span className="eyebrow"><i /> TRES PASOS. TODO EL CAMINO.</span><h2>Así de <em>fácil.</em></h2></div>
        <div className="steps-grid"><article><span className="step-count">01</span><span className="step-icon"><CalendarDays size={19} /></span><h3>Elige cuándo</h3><p>Selecciona tus fechas y descubre qué coches están disponibles.</p></article><article><span className="step-count">02</span><span className="step-icon"><CarFront size={20} /></span><h3>Encuentra el tuyo</h3><p>Compara categorías y precios totales, sin letra pequeña.</p></article><article><span className="step-count">03</span><span className="step-icon"><ArrowRight size={19} /></span><h3>Confirma y disfruta</h3><p>Crea tu cuenta, confirma la reserva y empieza a planear.</p></article></div>
      </section>
    </main>
    <footer className="site-footer"><Brand footer /><span>Tu camino, a tu manera.</span><div className="footer-links"><a href="#flota">Nuestra flota</a><button onClick={() => setDialog("help")}>Ayuda</button><button onClick={() => setDialog("terms")}>Condiciones</button></div><span>© {new Date().getFullYear()} Brisa Rent a Car</span></footer>

    {dialog === "auth" && <AuthDialog mode={authMode} setMode={(mode) => { setAuthMode(mode); setAuthError(""); setAuthSuccess(""); }} onClose={() => setDialog(null)} onLogin={handleLogin} onRegister={handleRegister} busy={authBusy} error={authError} success={authSuccess} />}
    {dialog === "booking" && selectedCar && <BookingDialog key={selectedCar.vehicle.id} item={selectedCar} dates={dates} onClose={() => setDialog(null)} onEditDates={editBookingDates} onConfirm={confirmBooking} busy={bookingBusy} error={bookingError} />}
    {dialog === "trips" && <TripsDialog bookings={bookings} loading={loadingBookings} error={bookingsError} onClose={() => setDialog(null)} onCancel={cancelBooking} />}
    {dialog === "profile" && token && <ProfileDialog profile={profile} onClose={() => setDialog(null)} onLogout={signOut} />}
    {dialog === "admin" && token && profile?.role === "admin" && <AdminDialog token={token} onClose={() => setDialog(null)} notify={setToast} />}
    {dialog === "help" && <HelpDialog onClose={() => setDialog(null)} />}
    {dialog === "terms" && <TermsDialog onClose={() => setDialog(null)} />}
    {toast && <div className="toast-message" role="status"><Check size={17} />{toast}</div>}
  </>;
}
