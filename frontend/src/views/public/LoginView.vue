<!-- LOGIN — form → store auth → API → cookie → redirect por rol. -->

<script setup>
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
</script>