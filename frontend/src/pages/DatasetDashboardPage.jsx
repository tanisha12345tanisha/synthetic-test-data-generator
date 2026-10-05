import { useEffect, useState } from "react"
import { createSavedDataset, createSchemaVersion, deleteSavedDataset, listSavedDatasets, listSchemaVersions, restoreSchemaVersion, shareSavedDataset } from "../api/datasetStorageApi"

export default function DatasetDashboardPage({ onClose }) {
  const [items,setItems]=useState([]);const [name,setName]=useState("");const [selected,setSelected]=useState(null);const [versions,setVersions]=useState([]);const [error,setError]=useState("")
  async function load(){try{setItems((await listSavedDatasets()).items)}catch(e){setError(e.message)}}
  useEffect(()=>{
    let active=true
    listSavedDatasets()
      .then(data=>{if(active)setItems(data.items)})
      .catch(error=>{if(active)setError(error.message)})
    return()=>{active=false}
  },[])
  async function create(e){e.preventDefault();await createSavedDataset({name,schema_document:{columns:[]}});setName("");await load()}
  async function open(item){setSelected(item);setVersions(await listSchemaVersions(item.id))}
  async function saveVersion(){await createSchemaVersion(selected.id);setVersions(await listSchemaVersions(selected.id))}
  async function restore(id){await restoreSchemaVersion(selected.id,id);await open(selected)}
  async function remove(id){await deleteSavedDataset(id);if(selected?.id===id)setSelected(null);await load()}
  async function share(){const email=window.prompt("Email to share with");if(email)await shareSavedDataset(selected.id,{email,permission:"viewer"})}
  return <main className="min-h-screen bg-slate-100 p-6 dark:bg-slate-950"><div className="mx-auto max-w-6xl"><div className="flex items-center justify-between"><h1 className="text-3xl font-bold dark:text-white">Saved datasets</h1><button onClick={onClose} className="rounded-xl bg-slate-900 px-4 py-2 text-white">Back to generator</button></div>{error&&<p className="mt-4 text-red-600">{error}</p>}<form onSubmit={create} className="mt-6 flex gap-3"><input value={name} onChange={e=>setName(e.target.value)} required placeholder="Dataset name" className="flex-1 rounded-xl border px-4 py-3"/><button className="rounded-xl bg-blue-600 px-5 text-white">Create</button></form><div className="mt-6 grid gap-5 lg:grid-cols-2"><section className="space-y-3">{items.map(item=><article key={item.id} className="rounded-2xl bg-white p-5 shadow dark:bg-slate-900 dark:text-white"><button onClick={()=>open(item)} className="text-left text-xl font-semibold">{item.name}</button><p className="text-sm text-slate-500">{item.status} · revision {item.current_draft_revision}</p><button onClick={()=>remove(item.id)} className="mt-3 text-sm text-red-600">Delete</button></article>)}</section>{selected&&<section className="rounded-2xl bg-white p-5 shadow dark:bg-slate-900 dark:text-white"><h2 className="text-xl font-semibold">{selected.name} history</h2><div className="mt-4 flex gap-2"><button onClick={saveVersion} className="rounded-lg bg-blue-600 px-3 py-2 text-white">Save version</button><button onClick={share} className="rounded-lg border px-3 py-2">Share</button></div><div className="mt-4 space-y-2">{versions.map(v=><div key={v.id} className="flex items-center justify-between rounded-xl border p-3"><span>Version {v.version_number} · {v.trigger}</span><button onClick={()=>restore(v.id)} className="text-blue-600">Restore</button></div>)}</div></section>}</div></div></main>
}
