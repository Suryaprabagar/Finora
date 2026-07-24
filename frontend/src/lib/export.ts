export function downloadCSV(data: any[], filename: string) {
  if (!data || data.length === 0) return

  const headers = Object.keys(data[0])
  const csvRows = []

  csvRows.push(headers.join(','))

  for (const row of data) {
    const values = headers.map(header => {
      let val = row[header]
      if (val === null || val === undefined) val = ''
      else if (typeof val === 'object') val = JSON.stringify(val)
      const escaped = ('' + val).replace(/"/g, '""')
      return `"${escaped}"`
    })
    csvRows.push(values.join(','))
  }

  const csvString = csvRows.join('\n')
  const blob = new Blob([csvString], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  
  const a = document.createElement('a')
  a.setAttribute('hidden', '')
  a.setAttribute('href', url)
  a.setAttribute('download', `${filename}.csv`)
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
