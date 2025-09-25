const { createApp } = Vue;

createApp({
  data() {
    return {
      products: window.PRODUCTS || [],
      categories: window.CATEGORIES || [],
      selectedCategory: (window.CATEGORIES && window.CATEGORIES[0]) || null,
      selectedCategoryRight: (window.CATEGORIES && window.CATEGORIES[0]) || null,
      quantities: {},
      data_scadenza: "",
      codice_animale: ""
    };
  },
  created() {
    // Inizializza tutte le quantità a 0 (Vue 3: niente this.$set)
    for (const p of this.products) {
      this.quantities[p.id] = 0;
    }
   
  },
  computed: {
    filteredProducts() {
      if (!this.selectedCategory) return this.products;
      return this.products.filter(p => p.categoria === this.selectedCategory);
    }
  },
  methods: {
    selectCategory(cat) { this.selectedCategory = cat; },
    selectCategoryRight(cat) { this.selectedCategoryRight = cat; },
    increment(id) { this.quantities[id] = (this.quantities[id] || 0) + 1; },
    decrement(id) { this.quantities[id] = Math.max(0, (this.quantities[id] || 0) - 1); },
    
  }
}).mount('#app');
