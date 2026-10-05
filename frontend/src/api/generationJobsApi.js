import { apiRequest } from "./apiClient"
const json=(body)=>({method:"POST",body:JSON.stringify(body)})
export const listGenerationJobs=()=>apiRequest("/generation-jobs")
export const submitGenerationJob=(body)=>apiRequest("/generation-jobs",json(body))
export const cancelGenerationJob=(id)=>apiRequest(`/generation-jobs/${id}/cancel`,{method:"POST"})
export const retryGenerationJob=(id)=>apiRequest(`/generation-jobs/${id}/retry`,{method:"POST"})
export const listGenerationOutputs=(id)=>apiRequest(`/generation-jobs/${id}/outputs`)
