function Pagination({ page, pageSize, total, onPageChange, onPageSizeChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="admin-pagination">
      <select value={pageSize} onChange={(e) => onPageSizeChange(Number(e.target.value))}>
        <option value={10}>10 / page</option>
        <option value={25}>25 / page</option>
        <option value={50}>50 / page</option>
      </select>

      <div className="admin-pagination-controls">
        <button onClick={() => onPageChange(page - 1)} disabled={page <= 1}>Prev</button>
        <span>Page {page} of {totalPages} ({total} total)</span>
        <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}>Next</button>
      </div>
    </div>
  )
}

export default Pagination
