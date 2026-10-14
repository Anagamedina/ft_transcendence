import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * 
This composable synchronizes filters with the URL. 
*Components will be able to read `q`, `filters`, 
*`page`, and `pageSize`, and then 
*call functions to modify the parameters.
*
* URL example:
* /admin/clients?q=hotel&status=ACTIVE&page=2&page_size=10
*/

export function useListQuery(options = {}) {
  const route = useRoute()
  const router = useRouter()

  const defaultPageSize = options.pageSize ?? 20

  const q = computed(() => {
    const value = route.query.q
    return typeof value === 'string' ? value : ''
  })

  const page = computed(() => {
    const value = Number(route.query.page ?? 1)
    return Number.isInteger(value) && value > 0 ? value : 1
  })

  const pageSize = computed(() => {
    const value = Number(route.query.page_size ?? defaultPageSize)
    return Number.isInteger(value) && value > 0 ? value : defaultPageSize
  })

  const filters = computed(() => {
    const result = {}

    for (const [key, value] of Object.entries(route.query)) {
      if (['q', 'page', 'page_size'].includes(key)) continue

      if (typeof value === 'string' && value !== '') {
        result[key] = value
      }
    }

    return result
  })

  async function updateQuery(patch = {}) {
    const query = { ...route.query }

    for (const [key, value] of Object.entries(patch)) {
      if (value === null || value === undefined || value === '') {
        delete query[key]
      } else {
        query[key] = String(value)
      }
    }

    // Any search/filter change resets pagination unless page was explicitly set.
    if (
      ('q' in patch || Object.keys(patch).some(
        (key) => !['page', 'page_size'].includes(key),
      )) &&
      !('page' in patch)
    ) {
      query.page = '1'
    }

    await router.replace({ query })
  }

  function setSearch(value) {
    return updateQuery({ q: value, page: 1 })
  }

  function setFilter(key, value) {
    return updateQuery({ [key]: value, page: 1 })
  }

  function setPage(value) {
    return updateQuery({ page: value })
  }

  function setPageSize(value) {
    return updateQuery({ page_size: value, page: 1 })
  }

  function clearFilters() {
    return router.replace({
      query: {
        page_size: String(defaultPageSize),
      },
    })
  }

  return {
    q,
    filters,
    page,
    pageSize,
    updateQuery,
    setSearch,
    setFilter,
    setPage,
    setPageSize,
    clearFilters,
  }
}