CREATE TABLE financial_data (
  	id int not null auto_increment primary key,
	symbol varchar(10) NOT NULL,
  	date date NOT NULL,
  	open_price decimal(20,2),
  	close_price decimal(20,2),
  	volume int
);