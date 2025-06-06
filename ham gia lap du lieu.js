// Hàm tạo dữ liệu ngẫu nhiên cho xe ô tô
function generateRandomCar() {
  const carBrands = ["Toyota", "Honda", "Ford", "BMW", "Mercedes", "Hyundai", "Mazda", "Kia", "Chevrolet", "Audi"];
  const carModels = ["Sedan", "SUV", "Hatchback", "Coupe", "Convertible", "Pickup", "Van"];
  const colors = ["Red", "Blue", "Black", "White", "Silver", "Green", "Gray"];
  const fuelTypes = ["Petrol", "Diesel", "Electric", "Hybrid"];
  const transmissionTypes = ["Automatic", "Manual"];
  
  const randomBrand = carBrands[Math.floor(Math.random() * carBrands.length)];
  const randomModel = carModels[Math.floor(Math.random() * carModels.length)];
  const randomColor = colors[Math.floor(Math.random() * colors.length)];
  const randomFuel = fuelTypes[Math.floor(Math.random() * fuelTypes.length)];
  const randomTransmission = transmissionTypes[Math.floor(Math.random() * transmissionTypes.length)];
  const randomYear = Math.floor(Math.random() * 24) + 2000; // Năm sản xuất từ 2000 đến 2023
  const randomPrice = Math.floor(Math.random() * 50000) + 10000; // Giá từ 10,000 đến 60,000

  return {
    brand: randomBrand,
    model: randomModel,
    color: randomColor,
    fuelType: randomFuel,
    transmission: randomTransmission,
    year: randomYear,
    priceUSD: randomPrice
  };
}